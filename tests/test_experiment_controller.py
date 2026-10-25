from core.experiment_controller import choose_experiment_action, record_experiment_result


def test_experiment_controller_selects_one_read_only_search():
    result = choose_experiment_action(
        {
            "status": "ready",
            "title": "Next experiment for demo",
            "hypothesis": "one assumption should be tested",
        },
        ["web_search"],
    )

    assert result.status == "ready"
    assert result.action == "web_search"
    assert len(result.action_input["query"]) <= 300


def test_experiment_controller_blocks_without_search_capability():
    result = choose_experiment_action(
        {"status": "ready", "title": "demo"},
        ["record_observation"],
    )

    assert result.status == "blocked"
    assert result.action is None


def test_experiment_result_completes_after_bounded_search():
    result = record_experiment_result(
        {"status": "ready", "title": "demo"},
        "web_search",
        "Search results recorded.",
    )

    assert result["status"] == "completed"
    assert result["action"] == "web_search"


def test_experiment_result_blocks_on_failed_search():
    result = record_experiment_result(
        {"status": "ready", "title": "demo"},
        "web_search",
        "Search failed: timeout",
    )

    assert result["status"] == "blocked"
