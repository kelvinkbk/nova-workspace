from datetime import datetime, timezone


MAX_REAL_WORLD_VALIDATION_REQUEST_HISTORY = 20


def record_real_world_validation_request(
    build_plan: dict,
    packet: dict,
    *,
    integrity: dict | None = None,
) -> dict:
    """Append a bounded audit record for a real-world validation request packet."""
    if not isinstance(build_plan, dict):
        return packet

    history = build_plan.setdefault("real_world_validation_request_history", [])
    if not isinstance(history, list):
        history = []
        build_plan["real_world_validation_request_history"] = history

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": str(packet.get("status") or "unknown"),
        "action": packet.get("action"),
        "purpose": str(packet.get("purpose") or ""),
        "required_capabilities": list(packet.get("required_capabilities") or []),
        "constraints": list(packet.get("constraints") or []),
        "blockers": list(packet.get("blockers") or []),
        "side_effects_allowed": bool(packet.get("side_effects_allowed")),
        "execution_status": str(packet.get("execution_status") or "unknown"),
        "request_fingerprint": str(packet.get("request_fingerprint") or ""),
        "integrity_valid": bool((integrity or {}).get("valid", True)),
        "integrity_issues": list((integrity or {}).get("issues") or []),
    }
    history.append(entry)

    if len(history) > MAX_REAL_WORLD_VALIDATION_REQUEST_HISTORY:
        del history[:-MAX_REAL_WORLD_VALIDATION_REQUEST_HISTORY]

    return entry


def real_world_validation_request_history(build_plan: dict) -> list[dict]:
    if not isinstance(build_plan, dict):
        return []
    history = build_plan.get("real_world_validation_request_history")
    if not isinstance(history, list):
        return []
    return [item for item in history if isinstance(item, dict)]
