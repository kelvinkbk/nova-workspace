from database.memory_repository import load_working_memory, save_working_memory
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_build_plan_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    memory = WorkingMemory(
        current_goal="software income",
        build_plan={
            "title": "Simple SaaS",
            "objective": "Smallest testable build",
            "deliverables": ["implementation", "tests"],
            "files": ["app/", "tests/"],
            "implementation_steps": ["build", "test"],
            "test_strategy": ["unit test"],
            "acceptance_criteria": ["zero-cost", "measurable"],
            "constraints": ["No owner capital."],
        },
    )
    save_working_memory(memory)

    loaded = load_working_memory()
    assert loaded.build_plan is not None
    assert loaded.build_plan["title"] == "Simple SaaS"
    assert loaded.build_plan["acceptance_criteria"] == ["zero-cost", "measurable"]
