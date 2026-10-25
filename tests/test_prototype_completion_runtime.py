from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_completed_prototype_freezes_mutation_actions(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    memory = WorkingMemory(
        current_goal="validated build",
        build_plan={
            "title": "demo",
            "status": "sandbox_complete",
            "scaffold_path": "builds/demo",
            "prototype_gate": {"status": "sandbox_complete"},
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "modify completed prototype",
            "validated build",
            ["change prototype"],
            "sandbox_write",
            "model choice",
            {"path": "builds/demo/app.py", "content": "bad"},
        ),
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "sandbox_write"],
    )

    assert result["decision"] == "record_observation"
    assert "mutation actions are frozen" in result["reflection"]
