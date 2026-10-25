from core.experiment_planner import create_next_experiment


def test_completed_prototype_gets_next_experiment():
    result = create_next_experiment(
        {
            "status": "sandbox_complete",
            "title": "demo",
            "success_metric": "one demand signal",
        }
    )

    assert result is not None
    assert result.status == "ready"
    assert result.title == "Next experiment for demo"
    assert "one unresolved assumption" in result.hypothesis
    assert result.success_metric == "one demand signal"
    assert "Rs 0 owner funding." in result.constraints


def test_incomplete_prototype_gets_no_experiment():
    assert create_next_experiment({"status": "reviewed", "title": "demo"}) is None
