from dataclasses import dataclass


@dataclass(frozen=True)
class PrototypeHandoff:
    status: str
    title: str
    completed_at_status: str
    next_action: str
    constraints: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "title": self.title,
            "completed_at_status": self.completed_at_status,
            "next_action": self.next_action,
            "constraints": list(self.constraints),
        }


def create_prototype_handoff(build_plan: dict | None) -> PrototypeHandoff | None:
    plan = build_plan if isinstance(build_plan, dict) else {}
    if plan.get("status") != "sandbox_complete":
        return None

    title = str(plan.get("title") or "Untitled prototype").strip()
    return PrototypeHandoff(
        status="ready_for_next_experiment",
        title=title,
        completed_at_status="sandbox_complete",
        next_action=(
            "Use the completed sandbox prototype as evidence; define the next bounded "
            "experiment instead of modifying the frozen prototype."
        ),
        constraints=(
            "Keep the completed prototype immutable.",
            "Do not deploy to production automatically.",
            "Do not spend owner capital.",
            "Do not perform financial, payment, credential, or external side effects.",
        ),
    )
