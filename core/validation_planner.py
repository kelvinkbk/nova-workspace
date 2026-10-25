from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationPlan:
    title: str
    hypothesis: str
    cost_ceiling: str
    steps: tuple[str, ...]
    success_criteria: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "hypothesis": self.hypothesis,
            "cost_ceiling": self.cost_ceiling,
            "steps": list(self.steps),
            "success_criteria": list(self.success_criteria),
            "blockers": list(self.blockers),
            "status": "ready",
            "step_index": 0,
            "observations": [],
        }


def build_validation_plan(selected: dict | None, evidence: list[dict] | None = None) -> ValidationPlan | None:
    if not selected or selected.get("status") != "selected":
        return None

    title = str(selected.get("title") or "Selected opportunity").strip()
    evidence = evidence or []
    has_monetization = any(
        str(item.get("monetization") or "").lower() not in {"", "unknown", "not stated"}
        for item in evidence
    )
    has_zero_cost = any(
        "free/no-upfront" in str(item.get("startup_cost") or "").lower()
        or "zero start" in str(item.get("capital_fit") or "").lower()
        for item in evidence
    )

    blockers = []
    if not has_monetization:
        blockers.append("Monetization is not yet explicit enough.")
    if not has_zero_cost:
        blockers.append("A zero-cost-compatible startup path is not yet evidenced.")

    return ValidationPlan(
        title=title,
        hypothesis=(
            f"A small version of '{title}' can solve a real problem and attract a first legitimate user "
            "without requiring owner capital."
        ),
        cost_ceiling="₹0 owner funding",
        steps=(
            "Define one narrowly scoped user problem to solve.",
            "Find independent evidence that people actively have or pay to solve that problem.",
            "Identify the smallest useful product or service that can test the hypothesis.",
            "Prepare a zero-cost distribution path and a measurable call-to-action.",
            "Run the smallest permitted test and record demand, conversion, and blockers.",
        ),
        success_criteria=(
            "At least one concrete demand signal from a real target user.",
            "A clear path from the test to legitimate revenue without owner capital.",
            "No required paid dependency before the first validation result.",
        ),
        blockers=tuple(blockers),
    )
