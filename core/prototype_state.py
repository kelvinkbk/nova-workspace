from dataclasses import dataclass, field


@dataclass(frozen=True)
class PrototypeStateValidation:
    valid: bool
    status: str
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "status": self.status,
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
        }


def validate_prototype_state(build_plan: dict | None) -> PrototypeStateValidation:
    plan = build_plan if isinstance(build_plan, dict) else {}
    status = str(plan.get("status") or "ready").strip()

    if not plan:
        return PrototypeStateValidation(
            valid=True,
            status="empty",
            reasons=["No active prototype build plan is present."],
        )

    reasons: list[str] = []
    blockers: list[str] = []

    if status in {"scaffolded", "repair_applied", "tested", "verified", "reviewed"}:
        if str(plan.get("scaffold_path") or "").strip():
            reasons.append("Prototype artifact path is present.")
        else:
            blockers.append(f"Status '{status}' requires a scaffold path.")

    if status == "repair_applied":
        if int(plan.get("repair_attempts") or 0) >= 1:
            reasons.append("Repair attempt count is recorded.")
        else:
            blockers.append("Repair-applied status requires at least one recorded repair attempt.")
        if str(plan.get("repair_result") or "").strip():
            reasons.append("Repair result is recorded.")
        else:
            blockers.append("Repair-applied status requires a repair result.")

    if status == "tested":
        if str(plan.get("prototype_result") or "").strip():
            reasons.append("Smoke-test result is recorded.")
        else:
            blockers.append("Tested status requires a recorded smoke-test result.")

    if status == "verified":
        evaluation = plan.get("prototype_evaluation")
        if isinstance(evaluation, dict) and evaluation.get("status") == "verified":
            reasons.append("Acceptance evaluation is verified.")
        else:
            blockers.append("Verified status requires a passing acceptance evaluation.")

    if status == "reviewed":
        review = plan.get("prototype_review")
        evaluation = plan.get("prototype_evaluation")
        if isinstance(evaluation, dict) and evaluation.get("status") == "verified":
            reasons.append("Reviewed status retains a passing acceptance evaluation.")
        else:
            blockers.append("Reviewed status requires a passing acceptance evaluation.")
        if isinstance(review, dict) and review.get("status") == "reviewed":
            reasons.append("Structural prototype review is recorded.")
        else:
            blockers.append("Reviewed status requires a passing structural review.")

    if status == "sandbox_complete":
        gate = plan.get("prototype_gate")
        if isinstance(gate, dict) and gate.get("status") == "sandbox_complete":
            reasons.append("Sandbox completion gate is recorded.")
        else:
            blockers.append("Sandbox-complete status requires a passing completion gate.")

    allowed_statuses = {
        "ready",
        "scaffolded",
        "repair_applied",
        "tested",
        "test_failed",
        "verified",
        "reviewed",
        "review_required",
        "sandbox_complete",
    }
    if status not in allowed_statuses:
        blockers.append(f"Unknown prototype status '{status}'.")

    return PrototypeStateValidation(
        valid=not blockers,
        status=status,
        reasons=reasons,
        blockers=blockers,
    )
