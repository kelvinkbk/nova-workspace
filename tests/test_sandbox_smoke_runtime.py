from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_runtime_runs_scaffolded_prototype_smoke_test(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    initialize_database()

    root = tmp_path / "sandbox" / "builds" / "simple-saas"
    root.mkdir(parents=True)
    (root / "app.py").write_text(
        "print('prototype smoke ok')\n",
        encoding="utf-8",
    )

    memory = WorkingMemory(
        current_goal="validated build",
        build_decision={"status": "build_minimal", "title": "Simple SaaS"},
        build_spec={"title": "Simple SaaS"},
        build_plan={
            "title": "Simple SaaS",
            "status": "scaffolded",
            "scaffold_path": "builds/simple-saas",
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "test prototype",
            "validated build",
            ["run smoke test"],
            "record_observation",
            "model choice",
            {},
        ),
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=[
            "record_observation",
            "sandbox_run_python",
            "sandbox_build",
        ],
    )

    assert result["decision"] == "sandbox_run_python"
    assert "Sandbox execution passed" in result["action"]
    assert result["build_plan"]["status"] == "tested"
    assert "prototype smoke ok" in result["build_plan"]["prototype_result"]


def test_runtime_records_failed_prototype_test(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    initialize_database()

    root = tmp_path / "sandbox" / "builds" / "broken"
    root.mkdir(parents=True)
    (root / "app.py").write_text("raise RuntimeError('broken')\n", encoding="utf-8")

    memory = WorkingMemory(
        current_goal="validated build",
        build_decision={"status": "build_minimal", "title": "Broken"},
        build_spec={"title": "Broken"},
        build_plan={
            "title": "Broken",
            "status": "scaffolded",
            "scaffold_path": "builds/broken",
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "test prototype",
            "validated build",
            ["run smoke test"],
            "record_observation",
            "model choice",
            {},
        ),
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "sandbox_run_python"],
    )

    assert result["decision"] == "sandbox_run_python"
    assert "Sandbox execution failed" in result["action"]
    assert result["build_plan"]["status"] == "test_failed"
