from core.capability_request import create_capability_request
from core.capability_approval_history import record_capability_approval as record_approval_history


def store_capability_request(build_plan: dict, request: dict) -> dict:
    """
    Store a capability request as the current request.

    Any previous approval belongs to the previous request and is cleared so it
    cannot be accidentally reused for a newly generated request.
    """
    if not isinstance(build_plan, dict):
        return request

    previous = build_plan.get("capability_request")
    previous_approval = build_plan.get("capability_approval")

    if previous != request:
        build_plan.pop("capability_approval", None)
        build_plan.pop("capability_approval_integrity", None)

    build_plan["capability_request"] = request

    if isinstance(previous_approval, dict) and previous != request:
        revoked = {
            "status": "superseded",
            "decision": "supersede",
            "requested": list(previous_approval.get("requested") or previous.get("requested") or []),
            "activation_allowed": False,
            "reason": "A new capability request superseded the previous approval.",
            "request_fingerprint": str(previous_approval.get("request_fingerprint") or ""),
        }
        record_approval_history(build_plan, revoked)
        build_plan["capability_approval_history"] = build_plan.get(
            "capability_approval_history", []
        )
        build_plan["previous_capability_approval"] = revoked

    return request


def build_and_store_capability_request(
    build_plan: dict,
    requested: tuple[str, ...] | list[str],
    manifest,
) -> dict:
    request = create_capability_request(requested, manifest).to_dict()
    return store_capability_request(build_plan, request)
