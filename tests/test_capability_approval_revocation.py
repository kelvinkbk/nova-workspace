from core.capability_approval import record_capability_approval
from core.capability_approval_controller import apply_capability_approval
from core.capability_approval_integrity import verify_capability_approval
from core.capability_approval_revocation import revoke_capability_approval


def test_revoke_cancels_existing_approval_without_activation():
    build_plan = {
        "capability_request": {
            "status": "approval_required",
            "requested": ["real_world_user_interaction"],
            "unavailable": ["real_world_user_interaction"],
            "approval_required": True,
        }
    }
    apply_capability_approval(build_plan, "approve")

    result = revoke_capability_approval(build_plan)

    assert result["status"] == "revoked"
    assert result["activation_allowed"] is False
    assert build_plan["capability_approval"]["status"] == "revoked"


def test_revoked_approval_fails_integrity_check():
    request = {
        "status": "approval_required",
        "requested": ["real_world_user_interaction"],
        "unavailable": ["real_world_user_interaction"],
        "approval_required": True,
    }
    approval = record_capability_approval(request, "approve").to_dict()
    approval["status"] = "revoked"
    approval["decision"] = "revoke"

    result = verify_capability_approval(request, approval)

    assert result.valid is False


def test_revoke_without_pending_approval_fails_closed():
    result = revoke_capability_approval({})

    assert result["status"] == "rejected"
    assert result["activation_allowed"] is False
