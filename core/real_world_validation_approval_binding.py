from datetime import datetime

from core.capability_approval import capability_request_fingerprint
from core.capability_approval_expiration import approval_is_expired


def validate_real_world_validation_approval_binding(
    validation_packet: dict | None,
    capability_request: dict | None,
    approval: dict | None,
    now: datetime | None = None,
) -> dict:
    """Check that any capability approval is bound to the exact validation request capability set."""
    packet = validation_packet if isinstance(validation_packet, dict) else {}
    request = capability_request if isinstance(capability_request, dict) else {}
    approval = approval if isinstance(approval, dict) else {}

    issues: list[str] = []
    required = tuple(packet.get("required_capabilities") or [])
    requested = tuple(request.get("requested") or [])
    approved = tuple(approval.get("requested") or [])

    if required != requested:
        issues.append("Validation capabilities do not match the capability request.")
    if requested != approved:
        issues.append("Capability approval is not bound to the requested capabilities.")
    expected_fingerprint = capability_request_fingerprint(request) if request else ""
    if approval.get("request_fingerprint") != expected_fingerprint:
        issues.append("Capability approval fingerprint does not match the capability request.")
    if not approval:
        issues.append("No capability approval is present.")
    if approval.get("activation_allowed") is not False:
        issues.append("Capability approval cannot activate capabilities directly.")
    if approval and approval.get("status") != "approved_pending_activation":
        issues.append("Capability approval must be approved_pending_activation.")
    if approval and approval.get("decision") != "approve":
        issues.append("Capability approval decision must be approve.")
    if approval and approval_is_expired(approval, now=now):
        issues.append("Capability approval has expired.")
    if approval and packet.get("status") != "prepared":
        issues.append("Capability approval cannot remain valid for a non-prepared validation request.")

    return {"valid": not issues, "issues": issues}
