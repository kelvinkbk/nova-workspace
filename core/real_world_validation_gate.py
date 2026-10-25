from dataclasses import dataclass, field

from core.capability_manifest import CapabilityManifest


@dataclass(frozen=True)
class RealWorldValidationGate:
    status: str
    required_capabilities: tuple[str, ...]
    available_capabilities: tuple[str, ...]
    blockers: list[str] = field(default_factory=list)
    next_action: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "required_capabilities": list(self.required_capabilities),
            "available_capabilities": list(self.available_capabilities),
            "blockers": list(self.blockers),
            "next_action": self.next_action,
        }


def create_real_world_validation_gate(
    experiment_decision: dict | None,
    available_actions: list[str] | None = None,
    manifest: CapabilityManifest | None = None,
) -> RealWorldValidationGate:
    decision = experiment_decision if isinstance(experiment_decision, dict) else {}
    capability_manifest = manifest or CapabilityManifest()
    capabilities = set(available_actions or [])
    status = str(decision.get("status") or "inconclusive")

    required = ("real_world_user_interaction",)
    available = tuple(sorted(capability for capability in capability_manifest.to_dict() if capability_manifest.available(capability)))

    if status != "corroborated_signal":
        return RealWorldValidationGate(
            status="not_ready",
            required_capabilities=required,
            available_capabilities=tuple(sorted(capabilities)),
            blockers=[
                "A corroborated research signal is required before planning real-world demand validation."
            ],
            next_action="Continue research or reassess the opportunity without external side effects.",
        )

    blockers = [
        "No authorized real-world user interaction capability is currently available."
    ]
    return RealWorldValidationGate(
        status="blocked",
        required_capabilities=required,
        available_capabilities=available,
        blockers=blockers,
        next_action=(
            "Keep the prototype frozen. Do not claim demand or deploy; "
            "wait for a separately authorized real-world validation capability."
        ),
    )
