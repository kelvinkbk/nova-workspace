from dataclasses import dataclass, field


@dataclass(frozen=True)
class PrototypeGate:
    status: str
    next_action: str
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "next_action": self.next_action,
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
        }


def check_prototype_gate(build_plan: dict | None) -> PrototypeGate:
    plan = build_plan if isinstance(build_plan, dict) else {}
    evaluation = plan.get("prototype_evaluation")
    review = plan.get("prototype_review")

    reasons: list[str] = []
    blockers: list[str] = []

    if plan.get("status") == "reviewed":
        reasons.append("Prototype structural review completed.")
    else:
        blockers.append("Prototype has not completed structural review.")

    if isinstance(evaluation, dict) and evaluation.get("status") == "verified":
        reasons.append("Deterministic acceptance evaluation passed.")
    else:
        blockers.append("Prototype acceptance evaluation has not passed.")

    if isinstance(review, dict) and review.get("status") == "reviewed":
        reasons.append("Sandbox-only artifact review passed.")
    else:
        blockers.append("Sandbox artifact review has not passed.")

    if blockers:
        return PrototypeGate(
            status="blocked",
            next_action="Resolve prototype blockers before any further implementation.",
            reasons=reasons,
            blockers=blockers,
        )

    return PrototypeGate(
        status="sandbox_complete",
        next_action="Define the next bounded product experiment; do not perform production deployment.",
        reasons=reasons + [
            "Prototype is complete inside the isolated sandbox."
        ],
    )
