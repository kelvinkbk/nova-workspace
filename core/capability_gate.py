from dataclasses import dataclass


_ACTION_CAPABILITIES = {
    "web_search": "read_only_research",
    "http_get": "read_only_research",
    "sandbox_write": "sandbox_mutation",
    "sandbox_run_python": "sandbox_mutation",
    "sandbox_build": "sandbox_mutation",
    "sandbox_run_project_tests": "sandbox_mutation",
    "request_user_feedback": "real_world_user_interaction",
}


@dataclass(frozen=True)
class CapabilityDecision:
    action: str
    allowed: bool
    capability: str | None
    reason: str

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "allowed": self.allowed,
            "capability": self.capability,
            "reason": self.reason,
        }


def evaluate_capability(action: str, manifest) -> CapabilityDecision:
    capability = _ACTION_CAPABILITIES.get(action)

    if capability is None:
        return CapabilityDecision(
            action=action,
            allowed=True,
            capability=None,
            reason="Action does not require an external capability.",
        )

    if manifest.available(capability):
        return CapabilityDecision(
            action=action,
            allowed=True,
            capability=capability,
            reason=f"Required capability '{capability}' is available.",
        )

    return CapabilityDecision(
        action=action,
        allowed=False,
        capability=capability,
        reason=f"Required capability '{capability}' is unavailable.",
    )
