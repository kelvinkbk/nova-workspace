from datetime import datetime, timezone

from core.capability_approval import capability_request_fingerprint
from core.real_world_validation_approval_binding import (
    validate_real_world_validation_approval_binding,
)


def test_expired_approval_is_rejected_by_binding():
    request = {"requested": ["real_world_user_interaction"]}
    approval = {
        "requested": request["requested"],
        "activation_allowed": False,
        "request_fingerprint": capability_request_fingerprint(request),
        "status": "approved_pending_activation",
        "decision": "approve",
        "issued_at": "2026-10-08T10:00:00+00:00",
        "expires_at": "2026-10-08T11:00:00+00:00",
    }
    result = validate_real_world_validation_approval_binding(
        {"status": "prepared", "required_capabilities": request["requested"]},
        request,
        approval,
        now=datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Capability approval has expired." in result["issues"]
