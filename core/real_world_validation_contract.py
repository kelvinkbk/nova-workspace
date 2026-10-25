from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationRequestSpec:
    status: str
    purpose: str
    required_capabilities: tuple[str, ...]
    permitted_actions: tuple[str, ...]
    blockers: list[str] = field(default_factory=list)
    constraints: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "purpose": self.purpose,
            "required_capabilities": list(self.required_capabilities),
            "permitted_actions": list(self.permitted_actions),
            "blockers": list(self.blockers),
            "constraints": list(self.constraints),
        }


def create_validation_request_spec(
    experiment_decision: dict | None,
    capability_manifest,
) -> ValidationRequestSpec:
    decision = experiment_decision if isinstance(experiment_decision, dict) else {}
    status = str(decision.get("status") or "inconclusive").strip()

    required = ("real_world_user_interaction",)
    base_constraints = (
        "Do not alter the frozen prototype.",
        "Do not spend owner capital.",
        "Do not collect credentials or sensitive personal data.",
        "Do not claim demand without actual user evidence.",
    )

    if status != "corroborated_signal":
        return ValidationRequestSpec(
            status="not_ready",
            purpose="Real-world demand validation is not justified until research evidence is corroborated.",
            required_capabilities=required,
            permitted_actions=(),
            blockers=["Research signal is not corroborated."],
            constraints=base_constraints,
        )

    if not capability_manifest.available("real_world_user_interaction"):
        return ValidationRequestSpec(
            status="blocked",
            purpose="Validate real user demand using one narrowly scoped interaction.",
            required_capabilities=required,
            permitted_actions=(),
            blockers=["The required real_world_user_interaction capability is unavailable."],
            constraints=base_constraints,
        )

    return ValidationRequestSpec(
        status="ready",
        purpose="Validate real user demand using one narrowly scoped interaction.",
        required_capabilities=required,
        permitted_actions=("request_user_feedback",),
        blockers=[],
        constraints=base_constraints,
    )
