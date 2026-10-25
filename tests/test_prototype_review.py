from core.prototype_review import review_prototype


def test_review_prototype_accepts_expected_scaffold(tmp_path, monkeypatch):
    root = tmp_path / "sandbox"
    project = root / "builds" / "demo"
    project.mkdir(parents=True)
    for name in ("README.md", "app.py", "test_app.py"):
        (project / name).write_text("ok", encoding="utf-8")

    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", root)
    result = review_prototype({"scaffold_path": "builds/demo"})

    assert result.status == "reviewed"
    assert result.blockers == []
    assert result.files == ["README.md", "app.py", "test_app.py"]


def test_review_prototype_rejects_unexpected_file(tmp_path, monkeypatch):
    root = tmp_path / "sandbox"
    project = root / "builds" / "demo"
    project.mkdir(parents=True)
    for name in ("README.md", "app.py", "test_app.py", "secret.txt"):
        (project / name).write_text("ok", encoding="utf-8")

    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", root)
    result = review_prototype({"scaffold_path": "builds/demo"})

    assert result.status == "review_required"
    assert result.blockers
    assert "unexpected or missing files" in result.blockers[0]


def test_review_prototype_rejects_sandbox_escape(tmp_path, monkeypatch):
    root = tmp_path / "sandbox"
    root.mkdir()
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", root)

    result = review_prototype({"scaffold_path": "../outside"})

    assert result.status == "review_required"
    assert "escapes the sandbox" in result.blockers[0]
