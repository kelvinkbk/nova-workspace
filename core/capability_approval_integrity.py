from dataclasses import dataclass
from datetime import datetime, timezone

from core.capability_approval import capability_request_fingerprint


@dataclass(frozen=True)
class ApprovalIntegrityDecision:
    valid: bool
    reason: str

    def to_dict(self) -> dict:
        return {"valid": self.valid, "reason": self.reason}


def verify_capability_approval(
    request: dict | None,
    approval: dict | None,
    *,
    now: datetime | None = None,
) -> ApprovalIntegrityDecision:
    if not isinstance(request, dict):
        return ApprovalIntegrityDecision(False, "No valid capability request is present.")

    if not isinstance(approval, dict):
        return ApprovalIntegrityDecision(False, "No capability approval is present.")

    if approval.get("status") != "approved_pending_activation":
        return ApprovalIntegrityDecision(False, "Only an approved_pending_activation record can pass integrity verification.")

    if approval.get("decision") != "approve":
        return ApprovalIntegrityDecision(False, "Approval decision is not approve.")

    if bool(approval.get("activation_allowed")):
        return ApprovalIntegrityDecision(False, "Approval record cannot grant activation authority.")

    expected = capability_request_fingerprint(request)
    actual = str(approval.get("request_fingerprint") or "")
    if actual != expected:
        return ApprovalIntegrityDecision(False, "Approval no longer matches the current capability request.")

    issued_raw = str(approval.get("issued_at") or "")
    expires_raw = str(approval.get("expires_at") or "")
    if not issued_raw or not expires_raw:
        return ApprovalIntegrityDecision(False, "Approval has no valid freshness window.")

    try:
        issued_at = datetime.fromisoformat(issued_raw)
        expires_at = datetime.fromisoformat(expires_raw)
    except ValueError:
        return ApprovalIntegrityDecision(False, "Approval freshness timestamps are invalid.")

    if issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= issued_at:
        return ApprovalIntegrityDecision(False, "Approval expiry must be after its issue time.")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    if current < issued_at:
        return ApprovalIntegrityDecision(False, "Approval is not valid before its issue time.")

    if current >= expires_at:
        return ApprovalIntegrityDecision(False, "Approval has expired and requires a fresh approval.")

    return ApprovalIntegrityDecision(True, "Approval matches the current request, is fresh, and remains non-activating.")
