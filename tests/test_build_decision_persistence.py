from database.memory_repository import load_working_memory, save_working_memory
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_build_decision_persists(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    memory = WorkingMemory(
        current_goal="software income",
        build_decision={
            "status": "build_minimal",
            "title": "Simple SaaS",
            "scope": ["one workflow"],
            "reasons": ["demand"],
            "blockers": [],
            "next_action": "Define MVP",
        },
    )
    save_working_memory(memory)

    loaded = load_working_memory()
    assert loaded.build_decision is not None
    assert loaded.build_decision["status"] == "build_minimal"
    assert loaded.build_decision["title"] == "Simple SaaS"
