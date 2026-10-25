from core.capability_approval_controller import apply_capability_approval
from core.capability_approval_revocation import revoke_capability_approval


def _build_plan():
    return {
        "capability_request": {
            "status": "approval_required",
            "requested": ["real_world_user_interaction"],
            "unavailable": ["real_world_user_interaction"],
            "approval_required": True,
            "activation_allowed": False,
        }
    }


def test_second_decision_cannot_overwrite_existing_approval():
    build_plan = _build_plan()

    first = apply_capability_approval(build_plan, "approve")
    second = apply_capability_approval(build_plan, "deny")

    assert first["status"] == "approved_pending_activation"
    assert second["status"] == "rejected"
    assert build_plan["capability_approval"]["status"] == "approved_pending_activation"
    assert build_plan["capability_approval"]["activation_allowed"] is False
    assert build_plan["capability_lifecycle"]["valid"] is True
    assert build_plan["capability_activation_preflight"]["status"] == "blocked"
    assert build_plan["capability_activation_preflight"]["activation_allowed"] is False


def test_denial_cannot_be_replaced_by_approval():
    build_plan = _build_plan()

    first = apply_capability_approval(build_plan, "deny")
    second = apply_capability_approval(build_plan, "approve")

    assert first["status"] == "denied"
    assert second["status"] == "rejected"
    assert build_plan["capability_approval"]["status"] == "denied"


def test_revoked_approval_cannot_be_reapproved_for_same_request():
    build_plan = _build_plan()

    apply_capability_approval(build_plan, "approve")
    revoked = revoke_capability_approval(build_plan)
    second = apply_capability_approval(build_plan, "approve")

    assert revoked["status"] == "revoked"
    assert second["status"] == "rejected"
    assert build_plan["capability_approval"]["status"] == "revoked"


def test_expired_approval_is_materialized_and_cannot_be_reused():
    build_plan = _build_plan()
    approval = apply_capability_approval(build_plan, "approve")

    approval["expires_at"] = "2026-01-01T00:00:00+00:00"
    build_plan["capability_approval"] = approval

    second = apply_capability_approval(build_plan, "approve")

    assert second["status"] == "rejected"
    assert build_plan["capability_approval"]["status"] == "expired"
    assert build_plan["capability_approval"]["activation_allowed"] is False
    assert build_plan["capability_lifecycle"]["status"] == "expired"
