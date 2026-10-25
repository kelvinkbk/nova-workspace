from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from core.effect_intent import EffectIntent


def _canonical_payload(grant: "ScopedEffectGrant") -> str:
    return json.dumps(
        {
            "effect_id": grant.effect_id,
            "intent_fingerprint": grant.intent_fingerprint,
            "kind": grant.kind,
            "target": grant.target,
            "max_cost": grant.max_cost,
            "expires_at": grant.expires_at,
            "capability_request_fingerprint": grant.capability_request_fingerprint,
            "activation_allowed": grant.activation_allowed,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class ScopedEffectGrant:
    """Narrow authorization metadata; it never activates an effect."""

    effect_id: str
    intent_fingerprint: str
    kind: str
    target: str
    max_cost: float
    expires_at: str
    capability_request_fingerprint: str
    activation_allowed: bool
    grant_fingerprint: str

    def to_dict(self) -> dict:
        return {
            "effect_id": self.effect_id,
            "intent_fingerprint": self.intent_fingerprint,
            "kind": self.kind,
            "target": self.target,
            "max_cost": self.max_cost,
            "expires_at": self.expires_at,
            "capability_request_fingerprint": self.capability_request_fingerprint,
            "activation_allowed": self.activation_allowed,
            "grant_fingerprint": self.grant_fingerprint,
        }

    def verify_fingerprint(self) -> bool:
        return hashlib.sha256(
            _canonical_payload(self).encode("utf-8")
        ).hexdigest() == self.grant_fingerprint


def build_scoped_effect_grant(
    intent: EffectIntent,
    *,
    max_cost: float,
    expires_at: datetime,
    capability_request_fingerprint: str,
    activation_allowed: bool = False,
) -> ScopedEffectGrant:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    provisional = ScopedEffectGrant(
        effect_id=intent.effect_id,
        intent_fingerprint=intent.intent_fingerprint,
        kind=intent.kind,
        target=intent.target,
        max_cost=float(max_cost),
        expires_at=expires_at.isoformat(),
        capability_request_fingerprint=capability_request_fingerprint.strip(),
        activation_allowed=bool(activation_allowed),
        grant_fingerprint="",
    )
    fingerprint = hashlib.sha256(
        _canonical_payload(provisional).encode("utf-8")
    ).hexdigest()
    return ScopedEffectGrant(
        **{**provisional.__dict__, "grant_fingerprint": fingerprint}
    )


def validate_scoped_effect_grant(
    intent: EffectIntent | None,
    grant: ScopedEffectGrant | None,
    *,
    now: datetime | None = None,
) -> dict:
    if not isinstance(intent, EffectIntent):
        return {"valid": False, "issues": ["Effect intent is missing or invalid."]}
    if not isinstance(grant, ScopedEffectGrant):
        return {"valid": False, "issues": ["Scoped effect grant is missing or invalid."]}

    issues: list[str] = []
    if not grant.verify_fingerprint():
        issues.append("Scoped effect grant fingerprint does not match its contents.")
    if grant.effect_id != intent.effect_id:
        issues.append("Scoped effect grant is not bound to this effect.")
    if grant.intent_fingerprint != intent.intent_fingerprint:
        issues.append("Scoped effect grant is not bound to this intent fingerprint.")
    if grant.kind != intent.kind:
        issues.append("Scoped effect grant kind does not match the effect intent.")
    if grant.target != intent.target:
        issues.append("Scoped effect grant target does not match the effect intent.")
    if grant.max_cost < 0:
        issues.append("Scoped effect grant max_cost cannot be negative.")
    if intent.cost_limit > grant.max_cost:
        issues.append("Effect cost exceeds the scoped grant limit.")
    if grant.capability_request_fingerprint != intent.capability_request_fingerprint:
        issues.append("Scoped effect grant capability fingerprint does not match the effect intent.")
    if grant.activation_allowed is not False:
        issues.append("Scoped effect grant cannot activate effects directly.")

    try:
        expires = datetime.fromisoformat(grant.expires_at)
    except ValueError:
        issues.append("Scoped effect grant expiry timestamp is invalid.")
    else:
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        if current >= expires:
            issues.append("Scoped effect grant has expired.")

    return {"valid": not issues, "issues": issues}
