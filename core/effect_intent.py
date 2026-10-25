from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone


_EFFECT_KINDS = frozenset({
    "publish_static_site",
    "request_user_feedback",
})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _canonical_payload(intent: "EffectIntent") -> str:
    return json.dumps(
        {
            "kind": intent.kind,
            "target": intent.target,
            "payload_hash": intent.payload_hash,
            "purpose": intent.purpose,
            "cost_limit": intent.cost_limit,
            "reversibility": intent.reversibility,
            "expires_at": intent.expires_at,
            "capability_request_fingerprint": intent.capability_request_fingerprint,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class EffectIntent:
    """Typed description of a possible external effect; it never executes anything."""

    effect_id: str
    kind: str
    target: str
    payload_hash: str
    purpose: str
    cost_limit: float
    reversibility: str
    requested_at: str
    expires_at: str
    capability_request_fingerprint: str
    intent_fingerprint: str

    def to_dict(self) -> dict:
        return {
            "effect_id": self.effect_id,
            "kind": self.kind,
            "target": self.target,
            "payload_hash": self.payload_hash,
            "purpose": self.purpose,
            "cost_limit": self.cost_limit,
            "reversibility": self.reversibility,
            "requested_at": self.requested_at,
            "expires_at": self.expires_at,
            "capability_request_fingerprint": self.capability_request_fingerprint,
            "intent_fingerprint": self.intent_fingerprint,
        }

    def verify_fingerprint(self) -> bool:
        return hashlib.sha256(_canonical_payload(self).encode("utf-8")).hexdigest() == self.intent_fingerprint


def build_effect_intent(
    *,
    kind: str,
    target: str,
    payload_hash: str,
    purpose: str,
    cost_limit: float,
    reversibility: str,
    expires_at: datetime,
    capability_request_fingerprint: str,
    requested_at: datetime | None = None,
    effect_id: str | None = None,
) -> EffectIntent:
    now = requested_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    requested = now.isoformat()
    expiry = expires_at.isoformat()
    seed = "|".join((kind.strip(), target.strip(), payload_hash.strip(), requested))
    generated_id = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]

    provisional = EffectIntent(
        effect_id=effect_id or generated_id,
        kind=kind.strip(),
        target=target.strip(),
        payload_hash=payload_hash.strip(),
        purpose=purpose.strip(),
        cost_limit=float(cost_limit),
        reversibility=reversibility.strip(),
        requested_at=requested,
        expires_at=expiry,
        capability_request_fingerprint=capability_request_fingerprint.strip(),
        intent_fingerprint="",
    )
    fingerprint = hashlib.sha256(_canonical_payload(provisional).encode("utf-8")).hexdigest()
    return EffectIntent(**{**provisional.__dict__, "intent_fingerprint": fingerprint})


def validate_effect_intent(intent: EffectIntent | None, *, now: datetime | None = None) -> dict:
    if not isinstance(intent, EffectIntent):
        return {"valid": False, "issues": ["Effect intent is missing or invalid."]}

    issues: list[str] = []
    if intent.kind not in _EFFECT_KINDS:
        issues.append("Unknown effect kind is rejected.")
    if not intent.target:
        issues.append("Effect target is required.")
    if not _SHA256.fullmatch(intent.payload_hash):
        issues.append("Effect payload_hash must be a SHA-256 hex digest.")
    if not intent.purpose:
        issues.append("Effect purpose is required.")
    if intent.cost_limit < 0:
        issues.append("Effect cost_limit cannot be negative.")
    if intent.reversibility not in {"reversible", "irreversible"}:
        issues.append("Effect reversibility must be reversible or irreversible.")
    if not intent.capability_request_fingerprint:
        issues.append("Capability request fingerprint is required.")
    if not intent.verify_fingerprint():
        issues.append("Effect intent fingerprint does not match its contents.")

    try:
        expires = datetime.fromisoformat(intent.expires_at)
        requested = datetime.fromisoformat(intent.requested_at)
    except ValueError:
        issues.append("Effect intent timestamps are invalid.")
    else:
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if requested.tzinfo is None:
            requested = requested.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        if expires <= requested:
            issues.append("Effect expiry must be after request time.")
        if current >= expires:
            issues.append("Effect intent has expired.")

    return {"valid": not issues, "issues": issues}
