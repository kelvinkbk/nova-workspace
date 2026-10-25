from core.capability_request_history import (
    MAX_CAPABILITY_REQUEST_HISTORY,
    capability_request_history,
    record_capability_request,
)


def _request(status: str, index: int) -> dict:
    return {
        "status": status,
        "requested": ["real_world_user_interaction"],
        "unavailable": ["real_world_user_interaction"],
        "approval_required": True,
        "activation_allowed": False,
        "reason": f"reason-{index}",
    }


def test_capability_request_history_is_bounded():
    build_plan = {}
    for index in range(MAX_CAPABILITY_REQUEST_HISTORY + 5):
        record_capability_request(build_plan, _request("approval_required", index))

    history = capability_request_history(build_plan)

    assert len(history) == MAX_CAPABILITY_REQUEST_HISTORY
    assert history[0]["reason"] == "reason-5"
    assert history[-1]["reason"] == f"reason-{MAX_CAPABILITY_REQUEST_HISTORY + 4}"


def test_capability_request_history_is_safe_for_invalid_state():
    assert capability_request_history({}) == []
    assert capability_request_history({"capability_request_history": "bad"}) == []

    build_plan = {"capability_request_history": "bad"}
    entry = record_capability_request(build_plan, _request("blocked", 1))

    assert entry["status"] == "blocked"
    assert len(build_plan["capability_request_history"]) == 1
