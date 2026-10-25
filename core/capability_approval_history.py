from datetime import datetime, timezone


MAX_CAPABILITY_APPROVAL_HISTORY = 20


def record_capability_approval(
    build_plan: dict,
    approval: dict,
) -> dict:
    """Append a bounded audit record for a human capability decision."""
    if not isinstance(build_plan, dict):
        return approval

    history = build_plan.setdefault("capability_approval_history", [])
    if not isinstance(history, list):
        history = []
        build_plan["capability_approval_history"] = history

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": str(approval.get("status") or "unknown"),
        "decision": str(approval.get("decision") or "unknown"),
        "requested": list(approval.get("requested") or []),
        "activation_allowed": bool(approval.get("activation_allowed")),
        "reason": str(approval.get("reason") or ""),
        "request_fingerprint": str(approval.get("request_fingerprint") or ""),
        "issued_at": approval.get("issued_at"),
        "expires_at": approval.get("expires_at"),
    }
    history.append(entry)

    if len(history) > MAX_CAPABILITY_APPROVAL_HISTORY:
        del history[:-MAX_CAPABILITY_APPROVAL_HISTORY]

    return entry


def capability_approval_history(build_plan: dict) -> list[dict]:
    if not isinstance(build_plan, dict):
        return []
    history = build_plan.get("capability_approval_history")
    if not isinstance(history, list):
        return []
    return [item for item in history if isinstance(item, dict)]
