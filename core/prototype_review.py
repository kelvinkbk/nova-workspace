from dataclasses import dataclass, field
from pathlib import Path

from tools import sandbox


EXPECTED_FILES = frozenset({"README.md", "app.py", "test_app.py"})
MAX_REVIEW_FILE_BYTES = 32 * 1024


@dataclass(frozen=True)
class PrototypeReview:
    status: str
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "files": list(self.files),
        }


def review_prototype(build_plan: dict | None) -> PrototypeReview:
    plan = build_plan if isinstance(build_plan, dict) else {}
    scaffold_path = str(plan.get("scaffold_path") or "").strip()
    reasons: list[str] = []
    blockers: list[str] = []

    if not scaffold_path:
        return PrototypeReview(
            status="review_required",
            blockers=["Prototype scaffold path is missing."],
        )

    root = sandbox.SANDBOX_ROOT.resolve()
    target = (root / scaffold_path).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        return PrototypeReview(
            status="review_required",
            blockers=["Prototype scaffold escapes the sandbox boundary."],
        )

    if not target.is_dir():
        return PrototypeReview(
            status="review_required",
            blockers=["Prototype scaffold directory does not exist."],
        )

    discovered = sorted(
        item.name
        for item in target.iterdir()
        if item.is_file()
    )
    if set(discovered) != EXPECTED_FILES:
        blockers.append(
            "Prototype contains unexpected or missing files; expected only README.md, app.py, and test_app.py."
        )
    else:
        reasons.append("Prototype contains exactly the expected scaffold files.")

    oversized = []
    for name in discovered:
        path = target / name
        try:
            size = path.stat().st_size
        except OSError:
            oversized.append(name)
            continue
        if size > MAX_REVIEW_FILE_BYTES:
            oversized.append(name)

    if oversized:
        blockers.append(
            "Prototype file size limit exceeded: " + ", ".join(oversized) + "."
        )
    else:
        reasons.append("All prototype files are within the bounded file-size limit.")

    if blockers:
        return PrototypeReview(
            status="review_required",
            reasons=reasons,
            blockers=blockers,
            files=discovered,
        )

    return PrototypeReview(
        status="reviewed",
        reasons=reasons + [
            "Prototype remains entirely inside the isolated sandbox."
        ],
        files=discovered,
    )
