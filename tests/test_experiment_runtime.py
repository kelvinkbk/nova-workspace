from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_runtime_executes_one_next_experiment_without_mutating_prototype(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    memory = WorkingMemory(
        current_goal="validated build",
        build_plan={
            "title": "demo",
            "status": "sandbox_complete",
            "scaffold_path": "builds/demo",
            "prototype_evaluation": {"status": "verified"},
            "prototype_review": {"status": "reviewed"},
            "prototype_gate": {"status": "sandbox_complete"},
            "next_experiment": {
                "status": "ready",
                "title": "Next experiment for demo",
                "hypothesis": "one unresolved assumption",
            },
        },
    )

    monkeypatch.setattr(
        "core.runtime.web_search",
        lambda query: (
            "[BEGIN UNTRUSTED WEB SEARCH RESULTS]\n"
            "1. Example demand evidence\n"
            "   URL: https://example.com/demo\n"
            "[END UNTRUSTED WEB SEARCH RESULTS]"
        ),
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "run next experiment",
            "validated build",
            ["one bounded search"],
            "record_observation",
            "model choice",
            {},
        ),
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "web_search"],
    )

    assert result["decision"] == "web_search"
    assert "[BEGIN UNTRUSTED WEB SEARCH RESULTS]" in result["action"]
    assert result["build_plan"]["status"] == "sandbox_complete"
    assert result["build_plan"]["next_experiment"]["status"] == "completed"
    assert result["build_plan"]["followup_experiment"]["status"] == "ready"
    assert result["build_plan"]["prototype_history"][-1]["event"] == "next_experiment"


def test_runtime_does_not_start_experiment_without_ready_plan(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    memory = WorkingMemory(
        current_goal="validated build",
        build_plan={
            "title": "demo",
            "status": "sandbox_complete",
            "next_experiment": {
                "status": "completed",
                "title": "Next experiment for demo",
            },
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "observe",
            "validated build",
            [],
            "record_observation",
            "model choice",
            {},
        ),
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "web_search"],
    )

    assert result["decision"] == "record_observation"


def test_runtime_executes_only_one_followup_experiment(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    memory = WorkingMemory(
        current_goal="validated build",
        build_plan={
            "title": "demo",
            "status": "sandbox_complete",
            "scaffold_path": "builds/demo",
            "prototype_evaluation": {"status": "verified"},
            "prototype_review": {"status": "reviewed"},
            "prototype_gate": {"status": "sandbox_complete"},
            "next_experiment": {"status": "completed", "title": "first"},
            "followup_experiment": {
                "status": "ready",
                "title": "follow-up",
                "purpose": "independent evidence",
            },
            "followup_count": 0,
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "run follow-up",
            "validated build",
            ["one corroborating search"],
            "record_observation",
            "model choice",
            {},
        ),
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "web_search"],
    )

    assert result["decision"] == "web_search"
    assert result["build_plan"]["followup_experiment"]["status"] == "completed"
    assert result["build_plan"]["followup_count"] == 1
    packet = result["build_plan"]["real_world_validation_request_packet"]
    assert packet["execution_status"] == "not_executed"
    assert packet["side_effects_allowed"] is False
