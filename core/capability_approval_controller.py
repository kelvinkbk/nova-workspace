from core.capability_approval import record_capability_approval
from core.capability_approval_history import record_capability_approval as record_approval_history
from core.capability_approval_integrity import verify_capability_approval
from core.capability_activation_preflight import preflight_capability_activation
from core.capability_manifest import CapabilityManifest
from core.capability_lifecycle import validate_capability_lifecycle
from core.capability_approval_expiration import approval_is_expired, expire_capability_approval


_TERMINAL_APPROVAL_STATES = frozenset({
    "approved_pending_activation",
    "denied",
    "revoked",
})


def apply_capability_approval(
    build_plan: dict,
    decision: str,
    manifest: CapabilityManifest | None = None,
) -> dict:
    """
    Apply one external approval decision to the current pending request.

    A terminal approval state cannot be overwritten. A fresh capability request
    must be created before another decision can be applied.
    """
    if not isinstance(build_plan, dict):
        return {
            "status": "rejected",
            "reason": "Build plan state is invalid.",
            "activation_allowed": False,
        }

    request = build_plan.get("capability_request")
    if not isinstance(request, dict):
        return {
            "status": "rejected",
            "reason": "No capability request is pending.",
            "activation_allowed": False,
        }

    existing = build_plan.get("capability_approval")
    if (
        isinstance(existing, dict)
        and existing.get("status") == "approved_pending_activation"
        and approval_is_expired(existing)
    ):
        existing = expire_capability_approval(build_plan)
        record_approval_history(build_plan, existing)
        build_plan["capability_approval_integrity"] = {
            "valid": False,
            "reason": "Approval expired and requires a fresh approval.",
        }
        build_plan["capability_lifecycle"] = validate_capability_lifecycle(
            request,
            existing,
        ).to_dict()

    if isinstance(existing, dict) and existing.get("status") in _TERMINAL_APPROVAL_STATES | {"expired"}:
        integrity = verify_capability_approval(request, existing)
        if existing.get("status") == "approved_pending_activation" and integrity.valid:
            reason = "A valid approval already exists; create a fresh capability request before another decision."
        else:
            reason = "The current capability request already has a terminal approval state; create a fresh request."
        return {
            "status": "rejected",
            "decision": str(decision).strip().lower(),
            "requested": list(request.get("requested") or []),
            "activation_allowed": False,
            "reason": reason,
            "request_fingerprint": str(existing.get("request_fingerprint") or ""),
        }

    approval = record_capability_approval(request, decision)
    approval_dict = approval.to_dict()

    build_plan["capability_approval"] = approval_dict
    integrity = verify_capability_approval(request, approval_dict)
    build_plan["capability_approval_integrity"] = integrity.to_dict()
    preflight = preflight_capability_activation(
        request,
        approval_dict,
        manifest or CapabilityManifest(),
    )
    build_plan["capability_activation_preflight"] = preflight.to_dict()
    lifecycle = validate_capability_lifecycle(request, approval_dict)
    build_plan["capability_lifecycle"] = lifecycle.to_dict()
    record_approval_history(build_plan, approval_dict)
    return approval_dict
