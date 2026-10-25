from tools.sandbox import sandbox_write_file


def test_sandbox_write_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    result = sandbox_write_file("app/main.py", "print('ok')")

    assert "Sandbox file written" in result
    assert (tmp_path / "sandbox" / "app" / "main.py").read_text(encoding="utf-8") == "print('ok')"


def test_sandbox_write_blocks_escape(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    result = sandbox_write_file("../outside.py", "bad")

    assert "escapes the sandbox" in result


def test_sandbox_write_blocks_unsupported_file_type(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    result = sandbox_write_file("app/run.exe", "bad")

    assert "file type is not permitted" in result


def test_sandbox_write_blocks_oversized_content(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")
    result = sandbox_write_file("app/main.py", "x" * (32 * 1024 + 1))

    assert "exceeds" in result
