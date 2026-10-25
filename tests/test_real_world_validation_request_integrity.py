from core.real_world_validation_request_integrity import (
    validate_real_world_validation_request_integrity,
)


def _packet():
    return {
        "status": "prepared",
        "action": "request_user_feedback",
        "required_capabilities": ["real_world_user_interaction"],
        "side_effects_allowed": False,
        "execution_status": "not_executed",
    }


def _request():
    return {"requested": ["real_world_user_interaction"]}


def test_matching_request_is_valid():
    result = validate_real_world_validation_request_integrity(_packet(), _request())
    assert result == {"valid": True, "issues": []}


def test_capability_mismatch_fails_closed():
    result = validate_real_world_validation_request_integrity(
        _packet(), {"requested": ["browser"]}
    )
    assert result["valid"] is False
    assert "Required capabilities do not match the capability request." in result["issues"]


def test_side_effects_and_execution_are_rejected():
    packet = dict(_packet(), side_effects_allowed=True, execution_status="executed")
    result = validate_real_world_validation_request_integrity(packet, _request())
    assert result["valid"] is False
    assert len(result["issues"]) == 2


def test_blocked_request_cannot_have_action():
    packet = dict(_packet(), status="blocked", action="request_user_feedback")
    result = validate_real_world_validation_request_integrity(packet, _request())
    assert result["valid"] is False
    assert "Blocked or non-prepared validation requests cannot contain an action." in result["issues"]
