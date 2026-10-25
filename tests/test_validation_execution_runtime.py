from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def _validated_memory():
    plan = {
        "title": "Simple SaaS",
        "hypothesis": "Test",
        "cost_ceiling": "₹0 owner funding",
        "steps": ["a", "b", "c", "d", "e"],
        "success_criteria": ["demand"],
        "blockers": [],
        "status": "ready",
        "step_index": 0,
        "observations": [],
    }
    selected = {
        "status": "selected",
        "title": "Simple SaaS",
        "url": "https://example.com/saas",
        "validation": {"status": "validated"},
    }
    return WorkingMemory(
        current_goal="software income",
        current_task="Execute validation",
        selected_opportunity=selected,
        validation_plan=plan,
    )


def test_runtime_prioritizes_validation_controller(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    runtime = RuntimeState()
    runtime.start()
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "model thought",
            "software income",
            ["ignore this"],
            "record_observation",
            "model choice",
            {},
        ),
    )
    monkeypatch.setattr(
        runtime,
        "act",
        lambda decision, policy: "Useful demand evidence found.",
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=_validated_memory().to_dict(),
        available_actions=["record_observation", "memory_search", "web_search"],
    )

    assert result["decision"] == "memory_search"
    assert result["policy_allowed"] is True
    assert result["action"] == "Useful demand evidence found."

    from database.memory_repository import load_working_memory
    updated = load_working_memory()
    assert updated.validation_plan["step_index"] == 1
    assert updated.selected_opportunity["validation"]["status"] == "validated"


def test_runtime_marks_validation_blocked_after_research_steps(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    memory = _validated_memory()
    memory.validation_plan["step_index"] = 4
    memory.validation_plan["status"] = "ready"

    runtime = RuntimeState()
    runtime.start()
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "model thought",
            "software income",
            ["ignore this"],
            "web_search",
            "model choice",
            {"query": "unsafe model query"},
        ),
    )
    monkeypatch.setattr(
        runtime,
        "act",
        lambda decision, policy: "Observation recorded successfully.",
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "web_search"],
    )

    assert result["decision"] == "record_observation"
    from database.memory_repository import load_working_memory
    updated = load_working_memory()
    assert updated.validation_plan["status"] == "blocked"
