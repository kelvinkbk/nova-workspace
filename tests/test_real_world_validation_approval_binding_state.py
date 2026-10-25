from core.capability_approval import capability_request_fingerprint
from core.real_world_validation_approval_binding import (
    validate_real_world_validation_approval_binding,
)


def test_non_pending_approval_is_rejected():
    request = {"requested": ["real_world_user_interaction"]}
    approval = {
        "requested": request["requested"],
        "activation_allowed": False,
        "request_fingerprint": capability_request_fingerprint(request),
        "status": "denied",
        "decision": "deny",
    }
    result = validate_real_world_validation_approval_binding(
        {"status": "prepared", "required_capabilities": request["requested"]},
        request,
        approval,
    )
    assert result["valid"] is False
    assert "Capability approval must be approved_pending_activation." in result["issues"]
    assert "Capability approval decision must be approve." in result["issues"]
