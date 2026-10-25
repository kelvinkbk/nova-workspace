from core.prototype_gate import check_prototype_gate


def complete_plan() -> dict:
    return {
        "status": "reviewed",
        "prototype_evaluation": {"status": "verified"},
        "prototype_review": {"status": "reviewed"},
    }


def test_complete_prototype_reaches_sandbox_complete():
    result = check_prototype_gate(complete_plan())

    assert result.status == "sandbox_complete"
    assert result.blockers == []
    assert "do not perform production deployment" in result.next_action


def test_incomplete_prototype_is_blocked():
    result = check_prototype_gate({"status": "reviewed"})

    assert result.status == "blocked"
    assert len(result.blockers) == 2
