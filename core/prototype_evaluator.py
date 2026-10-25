from dataclasses import dataclass, field


@dataclass(frozen=True)
class PrototypeEvaluation:
    status: str
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "checks": dict(self.checks),
        }


def evaluate_prototype(
    build_plan: dict | None,
    smoke_result: str = "",
    project_test_result: str = "",
) -> PrototypeEvaluation:
    plan = build_plan if isinstance(build_plan, dict) else {}

    checks = {
        "build_plan_present": bool(plan),
        "objective_present": bool(str(plan.get("objective", "")).strip()),
        "deliverables_present": bool(plan.get("deliverables")),
        "implementation_steps_present": bool(plan.get("implementation_steps")),
        "test_strategy_present": bool(plan.get("test_strategy")),
        "acceptance_criteria_present": bool(plan.get("acceptance_criteria")),
        "zero_cost_constraint": any(
            any(
                marker in str(item).lower()
                for marker in ("zero-cost", "rs 0", "no owner capital", "no owner funding")
            )
            for item in (plan.get("constraints") or [])
        ),
        "smoke_test_passed": (
            smoke_result.startswith("Sandbox execution succeeded:")
            or str(plan.get("status", "")).lower() in {"tested", "verified"}
        ),
        "project_tests_passed": project_test_result.startswith(
            "Sandbox project tests passed"
        ),
    }

    reasons: list[str] = []
    blockers: list[str] = []

    if checks["build_plan_present"]:
        reasons.append("Build plan is present.")
    else:
        blockers.append("Build plan is missing.")

    required_plan_checks = (
        "objective_present",
        "deliverables_present",
        "implementation_steps_present",
        "test_strategy_present",
        "acceptance_criteria_present",
    )
    if all(checks[name] for name in required_plan_checks):
        reasons.append("Required implementation and acceptance fields are present.")
    else:
        blockers.append("Build plan is incomplete.")

    if checks["zero_cost_constraint"]:
        reasons.append("Prototype remains within the zero-owner-funding constraint.")
    else:
        blockers.append("Zero-cost owner-funding constraint is not explicit.")

    if checks["smoke_test_passed"]:
        reasons.append("Bounded smoke test passed.")
    else:
        blockers.append("Bounded smoke test has not passed.")

    if checks["project_tests_passed"]:
        reasons.append("Generated project test suite passed.")
    else:
        blockers.append("Generated project test suite has not passed.")

    status = "verified" if not blockers else "review_required"
    return PrototypeEvaluation(
        status=status,
        reasons=reasons,
        blockers=blockers,
        checks=checks,
    )
