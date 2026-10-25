from dataclasses import dataclass

from datetime import datetime

from core.capability_approval_expiration import approval_is_expired
from core.capability_approval_integrity import verify_capability_approval


@dataclass(frozen=True)
class CapabilityLifecycleDecision:
    valid: bool
    status: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "status": self.status,
            "reason": self.reason,
        }


def validate_capability_lifecycle(
    request: dict | None,
    approval: dict | None,
    *,
    now: datetime | None = None,
) -> CapabilityLifecycleDecision:
    if not isinstance(request, dict):
        return CapabilityLifecycleDecision(
            valid=False,
            status="invalid_request",
            reason="Capability request is missing or invalid.",
        )

    request_status = str(request.get("status") or "")

    if approval is None:
        if request_status == "approval_required":
            return CapabilityLifecycleDecision(
                valid=True,
                status="awaiting_approval",
                reason="Request is valid and awaiting an external approval decision.",
            )
        return CapabilityLifecycleDecision(
            valid=True,
            status="no_approval_needed",
            reason="Request does not require a pending approval record.",
        )

    if not isinstance(approval, dict):
        return CapabilityLifecycleDecision(
            valid=False,
            status="invalid_approval",
            reason="Capability approval is malformed.",
        )

    approval_status = str(approval.get("status") or "")

    if approval_status == "approved_pending_activation":
        if approval_is_expired(approval, now=now):
            return CapabilityLifecycleDecision(
                valid=True,
                status="expired",
                reason="Approval has expired and cannot grant activation; a fresh approval is required.",
            )
        integrity = verify_capability_approval(request, approval, now=now)
        if not integrity.valid:
            return CapabilityLifecycleDecision(
                valid=False,
                status="approval_integrity_failure",
                reason=integrity.reason,
            )
        return CapabilityLifecycleDecision(
            valid=True,
            status="approved_pending_activation",
            reason="Approval matches the request and remains non-activating.",
        )

    if approval_status in {"denied", "revoked", "superseded", "expired"}:
        return CapabilityLifecycleDecision(
            valid=not bool(approval.get("activation_allowed")),
            status=approval_status,
            reason="Terminal approval state cannot grant activation.",
        )

    return CapabilityLifecycleDecision(
        valid=False,
        status="unknown_approval_state",
        reason="Unknown approval state is rejected.",
    )
