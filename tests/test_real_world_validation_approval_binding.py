from core.capability_approval import capability_request_fingerprint
from core.real_world_validation_approval_binding import (
    validate_real_world_validation_approval_binding,
)


def _packet():
    return {
        "status": "prepared",
        "required_capabilities": ["real_world_user_interaction"],
    }


def _request():
    return {"requested": ["real_world_user_interaction"]}


def _approval():
    request = _request()
    return {
        "requested": ["real_world_user_interaction"],
        "activation_allowed": False,
        "request_fingerprint": capability_request_fingerprint(request),
        "status": "approved_pending_activation",
        "decision": "approve",
    }


def test_matching_binding_is_valid():
    result = validate_real_world_validation_approval_binding(
        _packet(), _request(), _approval()
    )
    assert result == {"valid": True, "issues": []}


def test_mismatched_approval_is_rejected():
    approval = {"requested": ["browser"], "activation_allowed": False}
    result = validate_real_world_validation_approval_binding(
        _packet(), _request(), approval
    )
    assert result["valid"] is False
    assert "Capability approval is not bound to the requested capabilities." in result["issues"]


def test_fingerprint_mismatch_is_rejected():
    approval = _approval()
    approval["request_fingerprint"] = "tampered"
    result = validate_real_world_validation_approval_binding(
        _packet(), _request(), approval
    )
    assert result["valid"] is False
    assert "Capability approval fingerprint does not match the capability request." in result["issues"]


def test_missing_approval_is_rejected():
    result = validate_real_world_validation_approval_binding(
        _packet(), _request(), None
    )
    assert result["valid"] is False
    assert "No capability approval is present." in result["issues"]


def test_non_prepared_validation_request_invalidates_approval():
    packet = {"required_capabilities": ["real_world_user_interaction"], "status": "blocked"}
    result = validate_real_world_validation_approval_binding(
        packet, _request(), _approval()
    )
    assert result["valid"] is False
    assert "Capability approval cannot remain valid for a non-prepared validation request." in result["issues"]


def test_activation_allowed_is_rejected():
    approval = {"requested": ["real_world_user_interaction"], "activation_allowed": True}
    result = validate_real_world_validation_approval_binding(
        _packet(), _request(), approval
    )
    assert result["valid"] is False
    assert "Capability approval cannot activate capabilities directly." in result["issues"]
