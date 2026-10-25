from dataclasses import dataclass


@dataclass(frozen=True)
class BuildSpecification:
    title: str
    problem_statement: str
    target_user: str
    mvp_scope: tuple[str, ...]
    distribution_path: str
    success_metric: str
    cost_ceiling: str
    known_constraints: tuple[str, ...]
    unknowns: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "problem_statement": self.problem_statement,
            "target_user": self.target_user,
            "mvp_scope": list(self.mvp_scope),
            "distribution_path": self.distribution_path,
            "success_metric": self.success_metric,
            "cost_ceiling": self.cost_ceiling,
            "known_constraints": list(self.known_constraints),
            "unknowns": list(self.unknowns),
        }


def build_minimal_spec(
    build_decision: dict | None,
    validation_plan: dict | None,
    evidence: list[dict] | None = None,
) -> BuildSpecification | None:
    if not isinstance(build_decision, dict) or build_decision.get("status") != "build_minimal":
        return None

    title = str(build_decision.get("title") or "Untitled opportunity").strip()
    evidence = evidence or []
    observations = (
        validation_plan.get("observations", [])
        if isinstance(validation_plan, dict)
        else []
    )
    observation_text = " ".join(
        str(item.get("result") or "")
        for item in observations
        if isinstance(item, dict)
    ).strip()

    target_user = "The narrowest user group explicitly supported by the collected evidence."
    problem_statement = (
        f"Validate one concrete problem associated with '{title}' before expanding scope."
    )
    unknowns = [
        "Exact target-user segment",
        "Precise MVP workflow",
        "First distribution channel",
    ]

    if observation_text:
        unknowns.append("Whether observed demand converts into a real user action")
    if any(
        str(item.get("difficulty") or "").lower() in {"advanced", "difficult", "technical"}
        for item in evidence
    ):
        unknowns.append("Whether implementation complexity can stay within the zero-cost constraint")

    return BuildSpecification(
        title=title,
        problem_statement=problem_statement,
        target_user=target_user,
        mvp_scope=tuple(build_decision.get("scope") or (
            "one narrowly scoped user problem",
            "one smallest useful workflow",
        )),
        distribution_path="Use one zero-cost channel already permitted to NOVA; do not purchase reach.",
        success_metric="One measurable user-demand signal before adding features or spending money.",
        cost_ceiling="Rs 0 owner funding",
        known_constraints=(
            "No owner capital.",
            "Only currently authorized NOVA capabilities may be used.",
            "Do not perform financial or other external side effects without a separately authorized capability.",
        ),
        unknowns=tuple(unknowns),
    )
