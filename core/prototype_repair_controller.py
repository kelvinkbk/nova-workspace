from dataclasses import dataclass
from pathlib import Path


_ALLOWED_REPAIR_FILES = frozenset({"app.py", "test_app.py"})
_MAX_REPAIR_CONTENT_BYTES = 32 * 1024


@dataclass(frozen=True)
class RepairControllerDecision:
    status: str
    action: str | None
    reason: str
    repair_attempts: int
    max_attempts: int = 1

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "repair_attempts": self.repair_attempts,
            "max_attempts": self.max_attempts,
        }


def choose_repair_action(build_plan: dict | None) -> RepairControllerDecision:
    plan = build_plan if isinstance(build_plan, dict) else {}
    attempts = int(plan.get("repair_attempts") or 0)
    max_attempts = 1

    if attempts >= max_attempts:
        return RepairControllerDecision(
            status="blocked",
            action=None,
            reason="Maximum bounded prototype repair attempts have been used.",
            repair_attempts=attempts,
            max_attempts=max_attempts,
        )

    failure = plan.get("prototype_failure")
    repair_plan = plan.get("prototype_repair_plan")
    if not isinstance(failure, dict) or not isinstance(repair_plan, dict):
        return RepairControllerDecision(
            status="blocked",
            action=None,
            reason="A structured failure diagnosis and repair plan are required.",
            repair_attempts=attempts,
            max_attempts=max_attempts,
        )

    return RepairControllerDecision(
        status="ready",
        action="sandbox_write",
        reason=(
            "Apply exactly one smallest sandbox-local repair based on the recorded "
            "prototype failure, then rerun the bounded tests."
        ),
        repair_attempts=attempts,
        max_attempts=max_attempts,
    )


def validate_repair_write(
    build_plan: dict | None,
    action_input: dict | None,
) -> tuple[dict | None, str | None]:
    plan = build_plan if isinstance(build_plan, dict) else {}
    data = dict(action_input or {})
    scaffold = str(plan.get("scaffold_path") or "").strip()
    path = str(data.get("path") or "").strip()
    content = data.get("content")

    if not scaffold:
        return None, "prototype scaffold path is missing"
    if not path:
        return None, "repair path is required"
    if not isinstance(content, str):
        return None, "repair content must be text"

    relative = Path(path)
    scaffold_path = Path(scaffold)
    if relative.is_absolute() or any(part in {".", ".."} for part in relative.parts):
        return None, "absolute or traversal repair paths are not allowed"

    if relative.parent != scaffold_path:
        return None, "repair must target exactly one file in the active scaffold"
    if relative.name not in _ALLOWED_REPAIR_FILES:
        return None, "only app.py or test_app.py may be repaired"
    if len(content.encode("utf-8")) > _MAX_REPAIR_CONTENT_BYTES:
        return None, f"repair content exceeds {_MAX_REPAIR_CONTENT_BYTES} bytes"

    return {"path": path, "content": content}, None
