from core.capability_approval_history import (
    MAX_CAPABILITY_APPROVAL_HISTORY,
    capability_approval_history,
    record_capability_approval,
)


def _approval(index: int) -> dict:
    return {
        "status": "approved_pending_activation",
        "decision": "approve",
        "requested": ["real_world_user_interaction"],
        "activation_allowed": False,
        "reason": f"reason-{index}",
    }


def test_approval_history_is_bounded():
    build_plan = {}
    for index in range(MAX_CAPABILITY_APPROVAL_HISTORY + 3):
        record_capability_approval(build_plan, _approval(index))

    history = capability_approval_history(build_plan)

    assert len(history) == MAX_CAPABILITY_APPROVAL_HISTORY
    assert history[0]["reason"] == "reason-3"


def test_approval_history_handles_invalid_state():
    assert capability_approval_history({}) == []
    assert capability_approval_history({"capability_approval_history": "bad"}) == []

    build_plan = {"capability_approval_history": "bad"}
    entry = record_capability_approval(build_plan, _approval(1))

    assert entry["decision"] == "approve"
    assert entry["activation_allowed"] is False
    assert len(build_plan["capability_approval_history"]) == 1
