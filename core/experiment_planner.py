from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentPlan:
    status: str
    title: str
    hypothesis: str
    scope: tuple[str, ...]
    success_metric: str
    evidence_source: str
    constraints: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "title": self.title,
            "hypothesis": self.hypothesis,
            "scope": list(self.scope),
            "success_metric": self.success_metric,
            "evidence_source": self.evidence_source,
            "constraints": list(self.constraints),
        }


def create_next_experiment(build_plan: dict | None) -> ExperimentPlan | None:
    plan = build_plan if isinstance(build_plan, dict) else {}
    if plan.get("status") != "sandbox_complete":
        return None

    title = str(plan.get("title") or "completed prototype").strip()
    metric = str(plan.get("success_metric") or "").strip()
    return ExperimentPlan(
        status="ready",
        title=f"Next experiment for {title}",
        hypothesis=(
            f"one unresolved assumption around '{title}' can be tested "
            "without changing the frozen prototype."
        ),
        scope=(
            "Identify exactly one unresolved assumption from the completed build.",
            "Design one bounded evidence-gathering step.",
            "Record one measurable result before expanding scope.",
        ),
        success_metric=metric or "One measurable evidence signal is recorded.",
        evidence_source=(
            "Use only currently permitted read-only sources or sandbox observations."
        ),
        constraints=(
            "Do not modify the completed prototype.",
            "Do not deploy the prototype.",
            "Rs 0 owner funding.",
            "No banking, payment, credential, or external side effects.",
        ),
    )
