from pathlib import Path
import subprocess
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("NOVA Bridge")

# ============================================================
# SECURITY
# ============================================================

WORKSPACE = Path(r"E:\ai workspace").resolve()
CURRENT_DIRECTORY = WORKSPACE


def resolve_path(path: str = ".") -> Path:
    """
    Resolve either an absolute Windows path or a path relative to
    the currently selected directory.
    """

    requested = Path(path).expanduser()

    if requested.is_absolute():
        return requested.resolve()

    return (CURRENT_DIRECTORY / requested).resolve()


def find_venv_activate(start: Path) -> Path | None:
    """
    Find a .venv PowerShell activation script in the current directory
    or one of its parents.
    """

    current = start.resolve()

    while True:
        candidate = current / ".venv" / "Scripts" / "Activate.ps1"

        if candidate.exists():
            return candidate

        if current.parent == current:
            return None

        current = current.parent


# File tools now resolve relative paths from CURRENT_DIRECTORY and also
# accept absolute Windows paths, such as C:\\Users\\kelvin\\Projects\\app.
safe_path = resolve_path


# ============================================================
# MCP TOOLS
# ============================================================

@mcp.tool()
def nova_status() -> str:
    """Return the current NOVA MCP workspace status."""

    return (
        "NOVA MCP Bridge is online.\n"
        f"Workspace root: {WORKSPACE}\n"
        f"Current terminal directory: {CURRENT_DIRECTORY}\n"
        "File access: enabled\n"
        "Paths: absolute or current-directory relative"
    )


@mcp.tool()
def current_directory() -> str:
    """Return the currently selected Windows terminal directory."""
    return str(CURRENT_DIRECTORY)


@mcp.tool()
def set_directory(path: str) -> str:
    """
    Change the default directory used by terminal commands.

    Accepts an absolute Windows path, for example:
    C:\\Users\\kelvin\\Projects\\myapp
    """

    global CURRENT_DIRECTORY

    target = resolve_path(path)

    if not target.exists():
        return f"Directory does not exist: {target}"

    if not target.is_dir():
        return f"Not a directory: {target}"

    CURRENT_DIRECTORY = target

    return f"Current directory changed to: {CURRENT_DIRECTORY}"


@mcp.tool()
def list_files(path: str = ".") -> str:
    """
    List files and folders in the selected Windows directory.

    path may be relative to the current directory or an absolute path.
    """

    target = safe_path(path)

    if not target.exists():
        return f"Path does not exist: {path}"

    if not target.is_dir():
        return f"Not a directory: {path}"

    items = []

    for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        relative = item

        if item.is_dir():
            items.append(f"[DIR]  {relative}")
        else:
            size = item.stat().st_size
            items.append(f"[FILE] {relative} ({size} bytes)")

    if not items:
        return "(empty directory)"

    return "\n".join(items)


@mcp.tool()
def read_file(path: str) -> str:
    """
    Read a UTF-8 text file using a relative or absolute Windows path.
    """

    target = safe_path(path)

    if not target.exists():
        return f"File does not exist: {path}"

    if not target.is_file():
        return f"Not a file: {path}"

    # Safety limit for accidental huge reads
    max_size = 2 * 1024 * 1024

    if target.stat().st_size > max_size:
        raise ValueError(
            f"File is larger than 2 MB. Refusing to read automatically: {path}"
        )

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            "This does not appear to be a UTF-8 text file."
        )


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """
    Create or overwrite a UTF-8 text file using a relative or absolute path.

    Parent directories are created automatically.
    """

    target = safe_path(path)

    target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(content, encoding="utf-8")

    return f"File written successfully: {target}"


@mcp.tool()
def replace_in_file(
    path: str,
    old_text: str,
    new_text: str,
) -> str:
    """
    Replace an exact piece of text inside a UTF-8 file.

    The replacement must match exactly.
    """

    target = safe_path(path)

    if not target.exists():
        return f"File does not exist: {path}"

    if not target.is_file():
        return f"Not a file: {path}"

    content = target.read_text(encoding="utf-8")

    occurrences = content.count(old_text)

    if occurrences == 0:
        return "The requested old_text was not found."

    if occurrences > 1:
        return (
            f"Found {occurrences} occurrences. "
            "Refusing to edit because the match is not unique."
        )

    updated = content.replace(old_text, new_text, 1)

    target.write_text(updated, encoding="utf-8")

    return (
        f"File edited successfully: "
        f"{target}"
    )


@mcp.tool()
def create_directory(path: str) -> str:
    """
    Create a directory using a relative or absolute Windows path.
    """

    target = safe_path(path)

    target.mkdir(parents=True, exist_ok=True)

    return f"Directory created: {target}"


@mcp.tool()
def run_command(command: str, cwd: str = ".") -> str:
    """
    Run a PowerShell command in a selectable Windows directory.

    cwd may be relative to the current directory or an absolute path.
    Captures stdout, stderr, and the exit code.
    """

    working_dir = resolve_path(cwd)

    if not working_dir.exists():
        return f"Working directory does not exist: {cwd}"

    if not working_dir.is_dir():
        return f"Working path is not a directory: {cwd}"

    try:
        # Automatically activate a .venv in the selected project
        # or one of its parent directories when available.
        venv_activate = find_venv_activate(working_dir)
        utf8 = "$env:PYTHONIOENCODING='utf-8'; [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()"

        if venv_activate:
            activate = f"& '{venv_activate}'"
            full_command = f"{utf8}; {activate}; {command}"
        else:
            full_command = f"{utf8}; {command}"

        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-NonInteractive",
                "-Command",
                full_command,
            ],
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

        return (
            "COMMAND TIMED OUT after 300 seconds\n"
            f"Working directory: {working_dir}\n\n"
            f"STDOUT:\n{stdout[-10000:]}\n\n"
            f"STDERR:\n{stderr[-10000:]}"
        )
    except Exception as exc:
        return f"Failed to run command: {type(exc).__name__}: {exc}"

    stdout = completed.stdout or "(no stdout)"
    stderr = completed.stderr or "(no stderr)"

    return (
        f"EXIT CODE: {completed.returncode}\n"
        f"WORKING DIRECTORY: {working_dir}\n\n"
        f"STDOUT:\n{stdout[-10000:]}\n\n"
        f"STDERR:\n{stderr[-10000:]}"
    )


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
    )