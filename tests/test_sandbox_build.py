from tools.sandbox_build import build_scaffold


def test_build_scaffold_creates_minimal_project(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    result = build_scaffold({
        "title": "Simple SaaS",
        "status": "build_minimal",
    })

    root = tmp_path / "sandbox" / "builds" / "simple-saas"
    assert "Sandbox scaffold created" in result
    assert (root / "README.md").exists()
    assert (root / "app.py").exists()
    assert (root / "test_app.py").exists()


def test_build_scaffold_requires_build_plan(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    assert "no build plan" in build_scaffold(None).lower()
