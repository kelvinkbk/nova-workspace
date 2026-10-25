from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def _run_runtime(tmp_path, monkeypatch, project_name, app_code, test_code):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    initialize_database()

    root = tmp_path / "sandbox" / "builds" / project_name
    root.mkdir(parents=True)
    (root / "README.md").write_text("# prototype\n", encoding="utf-8")
    (root / "app.py").write_text(app_code, encoding="utf-8")
    (root / "test_app.py").write_text(test_code, encoding="utf-8")

    memory = WorkingMemory(
        current_goal="validated build",
        build_decision={"status": "build_minimal", "title": project_name},
        build_spec={"title": project_name},
        build_plan={
            "title": project_name,
            "status": "tested",
            "scaffold_path": f"builds/{project_name}",
            "prototype_result": "Sandbox execution passed: prototype-ready",
            "objective": "Build a minimal prototype.",
            "deliverables": ["Minimal implementation.", "Automated tests."],
            "implementation_steps": ["Create the smallest implementation."],
            "test_strategy": ["Run deterministic tests."],
            "acceptance_criteria": ["End-to-end reproducible."],
            "constraints": ["No owner capital."],
        },
    )

    runtime = RuntimeState()
    runtime.status = "ONLINE"
    monkeypatch.setattr(
        runtime,
        "think",
        lambda **kwargs: BrainDecision(
            "run tests",
            "validated build",
            ["run project tests"],
            "record_observation",
            "model choice",
            {},
        ),
    )

    return runtime.run_cycle(
        identity={"name": "NOVA"},
        working_memory=memory.to_dict(),
        available_actions=["record_observation", "sandbox_run_project_tests"],
    )


def test_runtime_runs_generated_project_tests_after_smoke_test(tmp_path, monkeypatch):
    result = _run_runtime(
        tmp_path,
        monkeypatch,
        "simple-saas",
        "def run():\n    return {'status': 'prototype-ready'}\n",
        "from app import run\n\ndef test_run():\n    assert run()['status'] == 'prototype-ready'\n",
    )
    assert result["decision"] == "sandbox_run_project_tests"
    assert "Sandbox project tests passed" in result["action"]
    assert result["build_plan"]["status"] == "sandbox_complete"
    assert result["build_plan"]["prototype_evaluation"]["status"] == "verified"
    assert result["build_plan"]["prototype_review"]["status"] == "reviewed"
    assert result["build_plan"]["prototype_gate"]["status"] == "sandbox_complete"


def test_runtime_records_failed_project_tests(tmp_path, monkeypatch):
    result = _run_runtime(
        tmp_path,
        monkeypatch,
        "broken",
        "def run():\n    return {'status': 'x'}\n",
        "def test_fail():\n    assert False\n",
    )
    assert result["decision"] == "sandbox_run_project_tests"
    assert "Sandbox project tests failed" in result["action"]
    assert result["build_plan"]["status"] == "test_failed"
    assert result["build_plan"]["prototype_evaluation"]["status"] == "review_required"
