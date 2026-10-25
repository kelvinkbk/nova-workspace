import re

from tools.sandbox import SANDBOX_ROOT, sandbox_write_file


MAX_TITLE_LENGTH = 100


def _slug(title: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return (clean or "untitled-product")[:60]


def build_scaffold(build_plan: dict | None) -> str:
    if not isinstance(build_plan, dict):
        return "Sandbox build denied: no build plan is active."
    if build_plan.get("status") not in {None, "ready", "build_minimal"}:
        return "Sandbox build denied: build plan is not ready for a minimal scaffold."

    title = str(build_plan.get("title") or "Untitled product").strip()[:MAX_TITLE_LENGTH]
    slug = _slug(title)
    prefix = f"builds/{slug}"

    readme = (
        f"# {title}\n\n"
        "NOVA generated this sandbox-only scaffold from a validated build plan.\n"
        "This is a prototype boundary: no production deployment or external side effect is performed.\n"
    )
    app = (
        f'''"""Minimal sandbox prototype for {title}."""\n\n'''
        "def run() -> dict:\n"
        f"    return {{'product': {title!r}, 'status': 'prototype-ready'}}\n\n"
        "if __name__ == '__main__':\n"
        "    print(run())\n"
    )
    tests = (
        "from app import run\n\n"
        "def test_run_returns_prototype_status():\n"
        "    result = run()\n"
        "    assert result['status'] == 'prototype-ready'\n"
    )

    root = SANDBOX_ROOT.resolve()
    target_dir = (root / prefix).resolve()
    try:
        target_dir.relative_to(root)
    except ValueError:
        return "Sandbox build denied: generated path escapes the sandbox."
    if target_dir.exists():
        return "Sandbox build denied: scaffold already exists; refusing to overwrite it."

    files = (
        (f"{prefix}/README.md", readme),
        (f"{prefix}/app.py", app),
        (f"{prefix}/test_app.py", tests),
    )
    results = [sandbox_write_file(path, content) for path, content in files]
    if any("denied" in result.lower() for result in results):
        return "Sandbox build failed: " + " | ".join(results)
    return (
        f"Sandbox scaffold created: {prefix}/ "
        "with README.md, app.py, and test_app.py."
    )
