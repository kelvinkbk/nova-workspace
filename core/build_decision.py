from dataclasses import dataclass


_DEMAND_SIGNALS = (
    "demand",
    "customers",
    "customer",
    "users",
    "user need",
    "problem",
    "paying",
    "paid",
    "revenue",
    "pricing",
    "willing to pay",
)
_ZERO_COST_SIGNALS = (
    "free",
    "no upfront",
    "zero start",
    "₹0",
    "zero-cost",
)


@dataclass(frozen=True)
class BuildDecision:
    status: str
    title: str | None
    scope: tuple[str, ...]
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    next_action: str

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "title": self.title,
            "scope": list(self.scope),
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "next_action": self.next_action,
        }


def _blob(plan: dict | None) -> str:
    if not isinstance(plan, dict):
        return ""
    observations = plan.get("observations") or []
    return " ".join(str(item.get("result") or "") for item in observations).lower()


def decide_first_build(
    selected: dict | None,
    validation_plan: dict | None,
    evidence: list[dict] | None = None,
) -> BuildDecision:
    evidence = evidence or []
    title = str((selected or {}).get("title") or "").strip() or None

    if not selected or selected.get("validation", {}).get("status") != "validated":
        return BuildDecision(
            "blocked",
            title,
            (),
            (),
            ("A validated opportunity is required before a build decision.",),
            "Continue opportunity validation.",
        )

    if not isinstance(validation_plan, dict):
        return BuildDecision(
            "blocked",
            title,
            (),
            (),
            ("No validation plan is available.",),
            "Create a validation plan first.",
        )

    monetization = any(
        str(item.get("monetization") or "").lower() not in {"", "unknown", "not stated"}
        for item in evidence
    )
    zero_cost = any(
        any(signal in str(item.get(field) or "").lower() for signal in _ZERO_COST_SIGNALS)
        for item in evidence
        for field in ("startup_cost", "capital_fit")
    )
    observed = _blob(validation_plan)
    demand = sum(signal in observed for signal in _DEMAND_SIGNALS)

    reasons = []
    blockers = []
    if monetization:
        reasons.append("Monetization is explicitly evidenced.")
    else:
        blockers.append("Monetization is not explicit enough.")

    if zero_cost:
        reasons.append("The evidence supports a zero-cost-compatible starting path.")
    else:
        blockers.append("A zero-cost-compatible starting path is not sufficiently evidenced.")

    if demand >= 2:
        reasons.append("Validation research contains multiple concrete demand signals.")
    else:
        blockers.append("Research has not produced enough concrete demand signals.")

    if str(validation_plan.get("status")) != "blocked":
        blockers.append("The research-only validation sequence is not complete.")

    if blockers:
        return BuildDecision(
            "do_not_build_yet",
            title,
            (),
            tuple(reasons),
            tuple(blockers),
            "Gather the missing evidence before building.",
        )

    return BuildDecision(
        "build_minimal",
        title,
        (
            "one narrowly scoped user problem",
            "one smallest useful workflow",
            "one zero-cost distribution path",
            "one measurable success metric",
        ),
        tuple(reasons),
        (),
        "Define and implement the smallest testable product without owner capital.",
    )
