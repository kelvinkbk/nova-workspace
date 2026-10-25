from datetime import datetime, timezone

from core.capability_approval_history import record_capability_approval


def approval_is_expired(
    approval: dict | None,
    *,
    now: datetime | None = None,
) -> bool:
    if not isinstance(approval, dict):
        return False
    if approval.get("status") != "approved_pending_activation":
        return False

    raw = str(approval.get("expires_at") or "")
    if not raw:
        return False

    try:
        expires_at = datetime.fromisoformat(raw)
    except ValueError:
        return False

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    return current >= expires_at


def expire_capability_approval(
    build_plan: dict,
    *,
    now: datetime | None = None,
) -> dict:
    """
    Materialize an expired approval as a terminal state.

    This never activates or modifies the capability manifest.
    """
    if not isinstance(build_plan, dict):
        return {
            "status": "rejected",
            "decision": "expire",
            "requested": [],
            "activation_allowed": False,
            "reason": "Build plan state is invalid.",
        }

    approval = build_plan.get("capability_approval")
    if not isinstance(approval, dict):
        return {
            "status": "rejected",
            "decision": "expire",
            "requested": [],
            "activation_allowed": False,
            "reason": "No capability approval is present.",
        }

    if not approval_is_expired(approval, now=now):
        return {
            "status": "rejected",
            "decision": "expire",
            "requested": list(approval.get("requested") or []),
            "activation_allowed": False,
            "reason": "Capability approval has not expired.",
            "request_fingerprint": str(approval.get("request_fingerprint") or ""),
        }

    expired = {
        "status": "expired",
        "decision": "expire",
        "requested": list(approval.get("requested") or []),
        "activation_allowed": False,
        "reason": "Capability approval expired; a fresh approval is required.",
        "request_fingerprint": str(approval.get("request_fingerprint") or ""),
        "issued_at": approval.get("issued_at"),
        "expires_at": approval.get("expires_at"),
    }
    build_plan["capability_approval"] = expired
    record_capability_approval(build_plan, expired)
    return expired
