from tools.sandbox_tests import sandbox_run_project_tests


def _make_project(root):
    project = root / "builds" / "simple-saas"
    project.mkdir(parents=True)
    (project / "app.py").write_text(
        "def run():\n    return {'status': 'prototype-ready'}\n",
        encoding="utf-8",
    )
    (project / "test_app.py").write_text(
        "from app import run\n\ndef test_run():\n    assert run()['status'] == 'prototype-ready'\n",
        encoding="utf-8",
    )
    return project


def test_project_tests_pass(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    project = _make_project(tmp_path / "sandbox")
    result = sandbox_run_project_tests("builds/simple-saas")
    assert "Sandbox project tests passed" in result
    assert "1 passed" in result


def test_project_tests_fail_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    project = _make_project(tmp_path / "sandbox")
    (project / "test_app.py").write_text(
        "def test_fail():\n    assert False\n",
        encoding="utf-8",
    )
    result = sandbox_run_project_tests("builds/simple-saas")
    assert "Sandbox project tests failed" in result


def test_project_tests_block_escape(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    assert "escapes the sandbox" in sandbox_run_project_tests("../outside")


def test_project_tests_require_test_file(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    project = tmp_path / "sandbox" / "builds" / "simple-saas"
    project.mkdir(parents=True)
    assert "test_app.py is missing" in sandbox_run_project_tests("builds/simple-saas")
