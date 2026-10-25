from core.real_world_validation_approval_enforcement import (
    validate_real_world_validation_approval_enforcement,
)


def test_valid_binding_requires_validated_enforcement():
    result = validate_real_world_validation_approval_enforcement(
        {"valid": True},
        {"status": "validated", "reason": "activation remains disabled"},
        {"status": "prepared", "side_effects_allowed": False, "execution_status": "not_executed"},
    )
    assert result == {"valid": True, "issues": []}


def test_invalid_binding_requires_blocked_enforcement():
    result = validate_real_world_validation_approval_enforcement(
        {"valid": False},
        {"status": "blocked", "reason": "binding failed"},
    )
    assert result == {"valid": True, "issues": []}


def test_contradictory_enforcement_fails():
    result = validate_real_world_validation_approval_enforcement(
        {"valid": False},
        {"status": "validated", "reason": "incorrect"},
    )
    assert result["valid"] is False
    assert "must produce blocked enforcement" in result["issues"][0]


def test_validated_enforcement_rejects_unsafe_packet():
    result = validate_real_world_validation_approval_enforcement(
        {"valid": True},
        {"status": "validated", "reason": "activation remains disabled"},
        {"status": "prepared", "side_effects_allowed": True, "execution_status": "not_executed"},
    )
    assert result["valid"] is False
    assert "side effects to remain disabled" in result["issues"][0]


def test_missing_enforcement_fails():
    result = validate_real_world_validation_approval_enforcement(
        {"valid": True},
        {},
    )
    assert result["valid"] is False
    assert len(result["issues"]) == 3
