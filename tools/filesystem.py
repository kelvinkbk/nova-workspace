from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def list_project_files() -> str:
    files = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(PROJECT_ROOT)
        # Don't expose runtime/cache/database internals.
        if any(
            part in {".git", ".venv", "__pycache__"}
            for part in relative.parts
        ):
            continue
        files.append(str(relative))
    files.sort()
    if not files:
        return "No project files found."
    return "\n".join(files)


def read_project_file(relative_path: str) -> str:
    requested = relative_path.strip()

    if not requested:
        return "File denied: a relative file path is required."

    candidate = (PROJECT_ROOT / requested).resolve()

    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError:
        return "File denied: path is outside the NOVA workspace."

    if not candidate.exists():
        return f"File not found: {requested}"

    if not candidate.is_file():
        return f"File denied: {requested} is not a file."

    try:
        return candidate.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"File denied: {requested} is not a UTF-8 text file."
    except OSError as exc:
        return f"File read failed: {exc}"
