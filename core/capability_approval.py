import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


_ALLOWED_DECISIONS = frozenset({"approve", "deny"})
DEFAULT_APPROVAL_TTL_SECONDS = 3600


def capability_request_fingerprint(request: dict) -> str:
    payload = {
        "status": str(request.get("status") or ""),
        "requested": sorted(
            str(item).strip()
            for item in (request.get("requested") or [])
            if str(item).strip()
        ),
        "unavailable": sorted(
            str(item).strip()
            for item in (request.get("unavailable") or [])
            if str(item).strip()
        ),
        "approval_required": bool(request.get("approval_required")),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CapabilityApproval:
    status: str
    decision: str
    requested: tuple[str, ...]
    activation_allowed: bool
    reason: str
    request_fingerprint: str
    issued_at: str | None = None
    expires_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "decision": self.decision,
            "requested": list(self.requested),
            "activation_allowed": self.activation_allowed,
            "reason": self.reason,
            "request_fingerprint": self.request_fingerprint,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }


def record_capability_approval(
    request: dict,
    decision: str,
    *,
    issued_at: datetime | None = None,
    ttl_seconds: int = DEFAULT_APPROVAL_TTL_SECONDS,
) -> CapabilityApproval:
    requested = tuple(
        str(item).strip()
        for item in (request.get("requested") or [])
        if str(item).strip()
    )
    normalized_decision = str(decision).strip().lower()
    request_fingerprint = capability_request_fingerprint(request)

    if request.get("status") != "approval_required":
        return CapabilityApproval(
            status="rejected",
            decision=normalized_decision,
            requested=requested,
            activation_allowed=False,
            reason="Only requests explicitly marked approval_required can receive an approval decision.",
            request_fingerprint=request_fingerprint,
        )

    if normalized_decision not in _ALLOWED_DECISIONS:
        return CapabilityApproval(
            status="rejected",
            decision=normalized_decision,
            requested=requested,
            activation_allowed=False,
            reason="Approval decision must be approve or deny.",
            request_fingerprint=request_fingerprint,
        )

    if normalized_decision == "deny":
        return CapabilityApproval(
            status="denied",
            decision="deny",
            requested=requested,
            activation_allowed=False,
            reason="Human approval was denied; no capability is activated.",
            request_fingerprint=request_fingerprint,
        )

    if ttl_seconds <= 0:
        return CapabilityApproval(
            status="rejected",
            decision="approve",
            requested=requested,
            activation_allowed=False,
            reason="Approval TTL must be greater than zero.",
            request_fingerprint=request_fingerprint,
        )

    start = issued_at or datetime.now(timezone.utc)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    expiry = start + timedelta(seconds=ttl_seconds)

    return CapabilityApproval(
        status="approved_pending_activation",
        decision="approve",
        requested=requested,
        activation_allowed=False,
        reason="Human approval was recorded, but approval alone cannot activate or modify the capability manifest.",
        request_fingerprint=request_fingerprint,
        issued_at=start.isoformat(),
        expires_at=expiry.isoformat(),
    )
