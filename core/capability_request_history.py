from datetime import datetime, timezone


MAX_CAPABILITY_REQUEST_HISTORY = 20


def record_capability_request(build_plan: dict, request: dict) -> dict:
    """Append a bounded, audit-friendly capability request record."""
    if not isinstance(build_plan, dict):
        return request

    history = build_plan.setdefault("capability_request_history", [])
    if not isinstance(history, list):
        history = []
        build_plan["capability_request_history"] = history

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": str(request.get("status") or "unknown"),
        "requested": list(request.get("requested") or []),
        "unavailable": list(request.get("unavailable") or []),
        "approval_required": bool(request.get("approval_required")),
        "activation_allowed": bool(request.get("activation_allowed")),
        "reason": str(request.get("reason") or ""),
    }
    history.append(entry)

    if len(history) > MAX_CAPABILITY_REQUEST_HISTORY:
        del history[:-MAX_CAPABILITY_REQUEST_HISTORY]

    return entry


def capability_request_history(build_plan: dict) -> list[dict]:
    if not isinstance(build_plan, dict):
        return []
    history = build_plan.get("capability_request_history")
    if not isinstance(history, list):
        return []
    return [item for item in history if isinstance(item, dict)]
