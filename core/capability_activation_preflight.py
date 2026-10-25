from dataclasses import dataclass

from core.capability_approval_integrity import verify_capability_approval


@dataclass(frozen=True)
class CapabilityActivationPreflight:
    status: str
    requested: tuple[str, ...]
    activation_allowed: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "requested": list(self.requested),
            "activation_allowed": self.activation_allowed,
            "reason": self.reason,
        }


def preflight_capability_activation(
    request: dict | None,
    approval: dict | None,
    manifest,
    *,
    activation_implemented: bool = False,
) -> CapabilityActivationPreflight:
    if not isinstance(request, dict) or not isinstance(approval, dict):
        return CapabilityActivationPreflight(
            status="blocked",
            requested=(),
            activation_allowed=False,
            reason="Activation requires a valid capability request and approval.",
        )

    integrity = verify_capability_approval(request, approval)
    requested = tuple(
        str(item).strip()
        for item in (request.get("requested") or [])
        if str(item).strip()
    )

    if not integrity.valid:
        return CapabilityActivationPreflight(
            status="blocked",
            requested=requested,
            activation_allowed=False,
            reason=f"Approval integrity failed: {integrity.reason}",
        )

    unavailable = tuple(
        capability for capability in requested
        if not manifest.available(capability)
    )
    if unavailable:
        return CapabilityActivationPreflight(
            status="blocked",
            requested=requested,
            activation_allowed=False,
            reason=f"Capability manifest does not currently provide: {', '.join(unavailable)}.",
        )

    if not activation_implemented:
        return CapabilityActivationPreflight(
            status="blocked",
            requested=requested,
            activation_allowed=False,
            reason="Approval is valid, but capability activation is not implemented in NOVA.",
        )

    return CapabilityActivationPreflight(
        status="ready",
        requested=requested,
        activation_allowed=True,
        reason="All activation preflight checks passed.",
    )
