from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_runtime_applies_one_bounded_repair_only_inside_active_scaffold(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    initialize_database()

    root = tmp_path / "sandbox" / "builds" / "demo"
    root.mkdir(parents=True)
    (root / "app.py").write_text("broken", encoding="utf-8")
    (root / "test_app.py").write_text("def test_fail():\n    assert False\n", encoding="utf-8")
    (root / "README.md").write_text("# demo\n", encoding="utf-8")

    memory = WorkingMemory(
        current_goal="validated build",
        build_decision={"status": "build_minimal", "title": "demo"},
        build_spec={"title": "demo"},
        build_plan={
            "title": "demo",
            "status": "test_failed",
            "scaffold_path": "builds/demo",
            "prototype_failure": {"failure_type": "syntax_error"},
            "prototype_repair_plan": {"status": "ready"},
            "repair_attempts": 0,
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "repair the failing prototype",
            "validated build",
            ["apply one bounded repair"],
            "sandbox_write",
            "Use the recorded repair plan.",
            {"path": "builds/demo/app.py", "content": "print('fixed')\n"},
        ),
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "sandbox_write", "sandbox_run_python"],
    )

    assert result["decision"] == "sandbox_write"
    assert result["policy_allowed"] is True
    assert "Sandbox file written" in result["action"]
    assert result["build_plan"]["status"] == "repair_applied"
    assert result["build_plan"]["repair_attempts"] == 1
    assert result["build_plan"]["prototype_history"][-1]["event"] == "repair"
    assert result["build_plan"]["prototype_history"][-1]["status"] == "applied"
    assert (root / "app.py").read_text(encoding="utf-8") == "print('fixed')\n"


def test_runtime_retests_repaired_prototype_before_project_tests(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    initialize_database()

    root = tmp_path / "sandbox" / "builds" / "demo"
    root.mkdir(parents=True)
    (root / "app.py").write_text(
        "def run():\n    return {'status': 'prototype-ready'}\n"
        "print(run())\n",
        encoding="utf-8",
    )
    (root / "test_app.py").write_text(
        "from app import run\n\ndef test_run():\n    assert run()['status'] == 'prototype-ready'\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# demo\n", encoding="utf-8")

    memory = WorkingMemory(
        current_goal="validated build",
        build_decision={"status": "build_minimal", "title": "demo"},
        build_spec={"title": "demo"},
        build_plan={
            "title": "demo",
            "status": "repair_applied",
            "scaffold_path": "builds/demo",
            "repair_attempts": 1,
            "repair_result": "Sandbox file written: builds/demo/app.py",
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "verify repaired prototype",
            "validated build",
            ["run bounded smoke test"],
            "record_observation",
            "Model choice",
            {},
        ),
    )

    result = runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "sandbox_run_python", "sandbox_run_project_tests"],
    )

    assert result["decision"] == "sandbox_run_python"
    assert "Sandbox execution passed" in result["action"]
    assert result["build_plan"]["status"] == "tested"
