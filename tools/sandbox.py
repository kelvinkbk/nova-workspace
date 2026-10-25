from pathlib import Path
import os
import subprocess
import sys


SANDBOX_ROOT = Path(__file__).resolve().parents[1] / "sandbox"
MAX_FILE_BYTES = 32 * 1024
MAX_SCRIPT_BYTES = 32 * 1024
MAX_OUTPUT_BYTES = 16 * 1024
DEFAULT_TIMEOUT_SECONDS = 10
ALLOWED_SUFFIXES = frozenset({".py", ".md", ".txt", ".json", ".html", ".css", ".js"})
BLOCKED_NAMES = frozenset({".env", ".git", "__pycache__"})


def _resolve_relative(path: str) -> tuple[Path | None, str | None]:
    if not isinstance(path, str) or not path.strip():
        return None, "path is required"

    relative = Path(path.strip())
    if relative.is_absolute():
        return None, "absolute paths are not allowed"
    if any(part in BLOCKED_NAMES for part in relative.parts):
        return None, "blocked path component"

    root = SANDBOX_ROOT.resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None, "path escapes the sandbox"
    return target, None


def sandbox_write_file(path: str, content: str) -> str:
    if not isinstance(content, str):
        return "Sandbox write denied: content must be text."

    target, error = _resolve_relative(path)
    if error:
        return f"Sandbox write denied: {error}"

    suffix = target.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return "Sandbox write denied: file type is not permitted."
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        return f"Sandbox write denied: file exceeds {MAX_FILE_BYTES} bytes."

    root = SANDBOX_ROOT.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Sandbox file written: {target.relative_to(root)}"


def sandbox_run_python(path: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> str:
    target, error = _resolve_relative(path)
    if error:
        return f"Sandbox execution denied: {error}"
    if target.suffix.lower() != ".py":
        return "Sandbox execution denied: only Python files may be executed."
    if not target.is_file():
        return "Sandbox execution denied: script does not exist."
    if target.stat().st_size > MAX_SCRIPT_BYTES:
        return f"Sandbox execution denied: script exceeds {MAX_SCRIPT_BYTES} bytes."
    if timeout_seconds <= 0 or timeout_seconds > DEFAULT_TIMEOUT_SECONDS:
        return (
            f"Sandbox execution denied: timeout must be between 0 and "
            f"{DEFAULT_TIMEOUT_SECONDS} seconds."
        )

    env = {}
    for key in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP"):
        value = os.environ.get(key)
        if value:
            env[key] = value

    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-u", str(target)],
            cwd=str(SANDBOX_ROOT.resolve()),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"Sandbox execution timed out after {timeout_seconds:g} seconds."

    output = completed.stdout or ""
    if completed.stderr:
        output += ("\n" if output else "") + completed.stderr

    if len(output.encode("utf-8")) > MAX_OUTPUT_BYTES:
        output = (
            output.encode("utf-8")[:MAX_OUTPUT_BYTES]
            .decode("utf-8", errors="replace")
            + "\n...[truncated]"
        )

    status = "passed" if completed.returncode == 0 else f"failed (exit code {completed.returncode})"
    return f"Sandbox execution {status}: {output}" if output else f"Sandbox execution {status}."
