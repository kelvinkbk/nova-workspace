from core.prototype_state import validate_prototype_state


def test_tested_state_requires_smoke_result():
    result = validate_prototype_state(
        {
            "status": "tested",
            "scaffold_path": "builds/demo",
        }
    )

    assert result.valid is False
    assert any("smoke-test result" in item for item in result.blockers)


def test_reviewed_state_requires_evaluation_and_review():
    result = validate_prototype_state(
        {
            "status": "reviewed",
            "scaffold_path": "builds/demo",
        }
    )

    assert result.valid is False
    assert len(result.blockers) == 2


def test_complete_reviewed_state_is_valid():
    result = validate_prototype_state(
        {
            "status": "reviewed",
            "scaffold_path": "builds/demo",
            "prototype_evaluation": {"status": "verified"},
            "prototype_review": {"status": "reviewed"},
        }
    )

    assert result.valid is True
    assert result.blockers == []


def test_unknown_status_is_invalid():
    result = validate_prototype_state({"status": "something_wrong"})

    assert result.valid is False
    assert "Unknown prototype status" in result.blockers[0]
