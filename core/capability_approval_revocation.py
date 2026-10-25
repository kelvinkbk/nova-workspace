from core.capability_approval_history import record_capability_approval as record_approval_history


def revoke_capability_approval(
    build_plan: dict,
    reason: str = "Human approval was revoked before activation.",
) -> dict:
    """
    Revoke a previously recorded approval.

    Revocation is state-only: it never activates or changes capabilities.
    """
    if not isinstance(build_plan, dict):
        return {
            "status": "rejected",
            "decision": "revoke",
            "requested": [],
            "activation_allowed": False,
            "reason": "Build plan state is invalid.",
        }

    request = build_plan.get("capability_request")
    approval = build_plan.get("capability_approval")

    if not isinstance(request, dict) or not isinstance(approval, dict):
        return {
            "status": "rejected",
            "decision": "revoke",
            "requested": [],
            "activation_allowed": False,
            "reason": "No capability approval is pending.",
        }

    requested = list(approval.get("requested") or request.get("requested") or [])
    revoked = {
        "status": "revoked",
        "decision": "revoke",
        "requested": requested,
        "activation_allowed": False,
        "reason": str(reason).strip() or "Human approval was revoked before activation.",
        "request_fingerprint": str(approval.get("request_fingerprint") or ""),
    }

    build_plan["capability_approval"] = revoked
    record_approval_history(build_plan, revoked)
    return revoked
