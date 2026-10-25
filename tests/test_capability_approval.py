from core.capability_approval import record_capability_approval


def _request():
    return {
        "status": "approval_required",
        "requested": ["real_world_user_interaction"],
        "activation_allowed": False,
    }


def test_approval_is_recorded_without_activation():
    result = record_capability_approval(_request(), "approve")

    assert result.status == "approved_pending_activation"
    assert result.activation_allowed is False


def test_denial_stays_disabled():
    result = record_capability_approval(_request(), "deny")

    assert result.status == "denied"
    assert result.activation_allowed is False


def test_invalid_decision_is_rejected():
    result = record_capability_approval(_request(), "maybe")

    assert result.status == "rejected"
    assert result.activation_allowed is False


def test_non_pending_request_cannot_be_approved():
    result = record_capability_approval(
        {"status": "already_available", "requested": ["read_only_research"]},
        "approve",
    )

    assert result.status == "rejected"
    assert result.activation_allowed is False
