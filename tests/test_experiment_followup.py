from core.experiment_followup import create_followup_experiment


def test_evidence_found_gets_one_corroborating_followup():
    result = create_followup_experiment(
        {"status": "completed", "title": "demo"},
        {"status": "evidence_found"},
        0,
    )

    assert result is not None
    assert result.status == "ready"
    assert "independent" in result.purpose
    assert "case study" in result.query


def test_inconclusive_gets_alternate_followup():
    result = create_followup_experiment(
        {"status": "completed", "title": "demo"},
        {"status": "inconclusive"},
        0,
    )

    assert result is not None
    assert "alternate" in result.purpose


def test_followup_budget_is_bounded_to_one():
    assert create_followup_experiment(
        {"status": "completed", "title": "demo"},
        {"status": "evidence_found"},
        1,
    ) is None


def test_incomplete_experiment_gets_no_followup():
    assert create_followup_experiment(
        {"status": "ready", "title": "demo"},
        {"status": "evidence_found"},
        0,
    ) is None
