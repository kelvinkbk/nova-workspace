from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_runtime_automatically_builds_ready_plan_in_sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    initialize_database()

    memory = WorkingMemory(
        current_goal="validated build",
        build_decision={"status": "build_minimal", "title": "Simple SaaS"},
        build_spec={
            "title": "Simple SaaS",
            "mvp_scope": ["one workflow"],
            "known_constraints": ["No owner capital."],
        },
        build_plan={
            "title": "Simple SaaS",
            "status": "ready",
            "scaffold_path": None,
            "files": ["app/"],
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "build",
            "validated build",
            ["build scaffold"],
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
            "sandbox_write",
            "sandbox_run_python",
            "sandbox_build",
        ],
    )

    assert result["decision"] == "sandbox_build"
    assert result["policy_allowed"] is True
    assert result["build_plan"]["status"] == "scaffolded"
    assert result["build_plan"]["scaffold_path"] == "builds/simple-saas"
    assert (tmp_path / "sandbox" / "builds" / "simple-saas" / "app.py").exists()
