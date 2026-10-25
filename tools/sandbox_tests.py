from pathlib import Path
import os
import subprocess
import sys

from tools import sandbox as sandbox_tools


def sandbox_run_project_tests(
    project_path: str,
    timeout_seconds: float = sandbox_tools.DEFAULT_TIMEOUT_SECONDS,
) -> str:
    if not isinstance(project_path, str) or not project_path.strip():
        return "Sandbox test denied: project path is required."
    if timeout_seconds <= 0 or timeout_seconds > sandbox_tools.DEFAULT_TIMEOUT_SECONDS:
        return (
            f"Sandbox test denied: timeout must be between 0 and "
            f"{sandbox_tools.DEFAULT_TIMEOUT_SECONDS} seconds."
        )

    relative = Path(project_path.strip())
    if relative.is_absolute():
        return "Sandbox test denied: absolute paths are not allowed."
    if any(part in sandbox_tools.BLOCKED_NAMES for part in relative.parts):
        return "Sandbox test denied: blocked path component."

    root = sandbox_tools.SANDBOX_ROOT.resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return "Sandbox test denied: path escapes the sandbox."
    if not target.is_dir():
        return "Sandbox test denied: project directory does not exist."

    test_file = target / "test_app.py"
    if not test_file.is_file():
        return "Sandbox test denied: expected test_app.py is missing."
    if test_file.stat().st_size > sandbox_tools.MAX_FILE_BYTES:
        return (
            f"Sandbox test denied: test_app.py exceeds "
            f"{sandbox_tools.MAX_FILE_BYTES} bytes."
        )

    env = {
        "PATH": os.environ.get("PATH", ""),
        "SystemRoot": os.environ.get("SystemRoot", ""),
        "WINDIR": os.environ.get("WINDIR", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-m", "pytest", "-q", "test_app.py"],
            cwd=str(target),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"Sandbox project tests timed out after {timeout_seconds:g} seconds."

    output = completed.stdout or ""
    if completed.stderr:
        output += ("\n" if output else "") + completed.stderr
    if len(output.encode("utf-8")) > sandbox_tools.MAX_OUTPUT_BYTES:
        output = (
            output.encode("utf-8")[:sandbox_tools.MAX_OUTPUT_BYTES]
            .decode("utf-8", errors="replace")
            + "\n...[truncated]"
        )

    status = "passed" if completed.returncode == 0 else f"failed (exit code {completed.returncode})"
    return (
        f"Sandbox project tests {status}: {output}"
        if output
        else f"Sandbox project tests {status}."
    )
