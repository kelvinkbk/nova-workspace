from database.memory_repository import (
    load_episodes,
    load_working_memory,
    save_episode,
    save_working_memory,
)
from database.schema import initialize_database
from memory.episodic import Episode
from memory.working import WorkingMemory


def test_working_memory_persistence():
    initialize_database()
    memory = WorkingMemory()
    memory.set_goal("Become financially self-sustaining")
    memory.set_task("Find the first legitimate opportunity")
    memory.set_project("NOVA")
    memory.add_note("Starting capital is ₹0")
    save_working_memory(memory)
    loaded = load_working_memory()
    assert loaded.current_goal == "Become financially self-sustaining"
    assert loaded.current_task == "Find the first legitimate opportunity"
    assert loaded.active_project == "NOVA"
    assert "Starting capital is ₹0" in loaded.notes

    memory.set_plan(
        ["Search opportunities", "Evaluate one"],
        memory.current_goal,
    )
    memory.advance_plan()
    save_working_memory(memory)
    loaded = load_working_memory()
    assert loaded.plan_steps == ["Search opportunities", "Evaluate one"]
    assert loaded.plan_index == 1
    assert loaded.current_task == "Evaluate one"

    memory.last_action = "web_search"
    memory.last_action_result = "Five results"
    memory.last_reflection = "Review them"
    memory.validation_plan = {
        "title": "Simple SaaS",
        "hypothesis": "Test demand",
        "cost_ceiling": "₹0 owner funding",
        "steps": ["Define problem", "Test demand"],
        "success_criteria": ["One real demand signal"],
        "blockers": [],
    }
    save_working_memory(memory)
    loaded = load_working_memory()
    assert loaded.last_action == "web_search"
    assert loaded.last_action_result == "Five results"
    assert loaded.last_reflection == "Review them"
    assert loaded.validation_plan["cost_ceiling"] == "₹0 owner funding"


def test_episode_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "database.connection.DATABASE_PATH",
        tmp_path / "test.db",
    )
    initialize_database()
    episode = Episode(
        event="NOVA memory system initialized",
        context="Memory persistence test",
        outcome="Episode successfully saved",
        importance=5,
    )
    episode_id = save_episode(episode)
    assert episode_id is not None
    episodes = load_episodes()
    assert len(episodes) >= 1
    assert episodes[0].event == "NOVA memory system initialized"
    assert episodes[0].importance == 5
