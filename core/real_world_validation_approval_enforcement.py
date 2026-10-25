def validate_real_world_validation_approval_enforcement(
    binding: dict | None,
    enforcement: dict | None,
    validation_packet: dict | None = None,
) -> dict:
    """Verify enforcement matches the binding and keeps validation side-effect free."""
    binding = binding if isinstance(binding, dict) else {}
    enforcement = enforcement if isinstance(enforcement, dict) else {}
    packet = validation_packet if isinstance(validation_packet, dict) else {}
    issues = []
    valid_binding = bool(binding.get("valid"))
    status = enforcement.get("status")
    reason = enforcement.get("reason")

    if status not in {"blocked", "validated"}:
        issues.append("Validation approval enforcement status is invalid.")
    if not isinstance(reason, str) or not reason.strip():
        issues.append("Validation approval enforcement reason is missing.")
    if valid_binding and status != "validated":
        issues.append("A valid validation approval binding must produce validated enforcement.")
    if not valid_binding and status != "blocked":
        issues.append("An invalid validation approval binding must produce blocked enforcement.")

    if status == "validated":
        if packet.get("status") != "prepared":
            issues.append("Validated enforcement requires a prepared validation request.")
        if packet.get("side_effects_allowed") is not False:
            issues.append("Validated enforcement requires side effects to remain disabled.")
        if packet.get("execution_status") != "not_executed":
            issues.append("Validated enforcement requires execution to remain not_executed.")

    return {"valid": not issues, "issues": issues}
