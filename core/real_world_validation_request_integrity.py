def validate_real_world_validation_request_integrity(
    packet: dict | None,
    capability_request: dict | None,
) -> dict:
    """Validate that a real-world request packet remains bound to its capability request."""
    packet = packet if isinstance(packet, dict) else {}
    capability_request = capability_request if isinstance(capability_request, dict) else {}

    issues: list[str] = []
    required = tuple(packet.get("required_capabilities") or [])
    requested = tuple(capability_request.get("requested") or [])

    if required != requested:
        issues.append("Required capabilities do not match the capability request.")
    if packet.get("side_effects_allowed") is not False:
        issues.append("Real-world validation requests must not permit side effects.")
    if packet.get("execution_status") != "not_executed":
        issues.append("Real-world validation requests must remain unexecuted.")
    if packet.get("status") == "prepared" and packet.get("action") != "request_user_feedback":
        issues.append("Prepared validation requests must use the feedback action.")
    if packet.get("status") != "prepared" and packet.get("action") is not None:
        issues.append("Blocked or non-prepared validation requests cannot contain an action.")

    return {
        "valid": not issues,
        "issues": issues,
    }
