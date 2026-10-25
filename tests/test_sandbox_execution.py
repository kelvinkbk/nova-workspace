from tools.sandbox import sandbox_run_python


def test_sandbox_run_python_executes_inside_sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    root = tmp_path / "sandbox"
    root.mkdir()
    (root / "hello.py").write_text("print('hello sandbox')", encoding="utf-8")

    result = sandbox_run_python("hello.py")

    assert "Sandbox execution passed" in result
    assert "hello sandbox" in result


def test_sandbox_run_python_blocks_escape(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    root = tmp_path / "sandbox"
    root.mkdir()

    result = sandbox_run_python("../outside.py")

    assert "escapes the sandbox" in result


def test_sandbox_run_python_blocks_non_python(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    root = tmp_path / "sandbox"
    root.mkdir()
    (root / "note.txt").write_text("print('no')", encoding="utf-8")

    result = sandbox_run_python("note.txt")

    assert "only Python files" in result


def test_sandbox_run_python_times_out(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    root = tmp_path / "sandbox"
    root.mkdir()
    (root / "slow.py").write_text(
        "import time\ntime.sleep(2)\n",
        encoding="utf-8",
    )

    result = sandbox_run_python("slow.py", timeout_seconds=0.2)

    assert "timed out" in result


def test_sandbox_run_python_blocks_long_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    root = tmp_path / "sandbox"
    root.mkdir()
    (root / "hello.py").write_text("print('ok')", encoding="utf-8")

    result = sandbox_run_python("hello.py", timeout_seconds=11)

    assert "timeout must be between" in result
