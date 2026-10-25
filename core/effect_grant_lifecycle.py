from __future__ import annotations

from datetime import datetime, timezone

from core.effect_grant import ScopedEffectGrant


_TERMINAL_STATES = frozenset({"revoked", "expired", "consumed"})


def validate_effect_grant_lifecycle(
    grant: ScopedEffectGrant | None,
    *,
    state: str = "active",
    now: datetime | None = None,
) -> dict:
    if not isinstance(grant, ScopedEffectGrant):
        return {"valid": False, "status": "invalid", "issues": ["Scoped effect grant is missing or invalid."]}

    issues: list[str] = []
    if state not in {"active", *_TERMINAL_STATES}:
        issues.append("Effect grant lifecycle state is invalid.")
    if grant.activation_allowed is not False:
        issues.append("Effect grant lifecycle cannot activate effects.")

    try:
        expires = datetime.fromisoformat(grant.expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        if state == "active" and current >= expires:
            return {
                "valid": True,
                "status": "expired",
                "issues": [],
                "can_use": False,
            }
    except ValueError:
        issues.append("Effect grant expiry timestamp is invalid.")

    if issues:
        return {"valid": False, "status": "invalid", "issues": issues, "can_use": False}

    return {
        "valid": True,
        "status": state,
        "issues": [],
        "can_use": state == "active",
    }


def transition_effect_grant_state(
    grant: ScopedEffectGrant | None,
    *,
    current_state: str,
    new_state: str,
) -> dict:
    terminal = _TERMINAL_STATES
    allowed = {
        "active": terminal,
    }
    if current_state not in {"active", *terminal} or new_state not in {"active", *terminal}:
        return {"valid": False, "status": "invalid", "issues": ["Effect grant lifecycle state is invalid."]}
    if current_state in terminal:
        return {"valid": False, "status": current_state, "issues": ["Terminal effect grant states cannot transition."]}
    if new_state not in allowed["active"]:
        return {"valid": False, "status": current_state, "issues": ["Effect grant transition is not permitted."]}
    return {"valid": True, "status": new_state, "issues": [], "can_use": False}
