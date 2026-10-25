from dataclasses import dataclass


_ALLOWED_CAPABILITIES = frozenset({
    "read_only_research",
    "sandbox_mutation",
    "real_world_user_interaction",
    "production_filesystem_write",
    "financial_accounts",
    "payments",
    "external_apis",
    "browser",
})


@dataclass(frozen=True)
class CapabilityRequest:
    status: str
    requested: tuple[str, ...]
    unavailable: tuple[str, ...]
    approval_required: bool
    activation_allowed: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "requested": list(self.requested),
            "unavailable": list(self.unavailable),
            "approval_required": self.approval_required,
            "activation_allowed": self.activation_allowed,
            "reason": self.reason,
        }


def create_capability_request(
    requested: tuple[str, ...] | list[str],
    manifest,
) -> CapabilityRequest:
    normalized = tuple(dict.fromkeys(str(item).strip() for item in requested if str(item).strip()))
    unknown = tuple(item for item in normalized if item not in _ALLOWED_CAPABILITIES)
    known = tuple(item for item in normalized if item in _ALLOWED_CAPABILITIES)
    unavailable = tuple(item for item in known if not manifest.available(item))

    if unknown:
        return CapabilityRequest(
            status="rejected",
            requested=normalized,
            unavailable=unknown,
            approval_required=False,
            activation_allowed=False,
            reason="Unknown capabilities are rejected; the manifest cannot be expanded by the agent.",
        )

    if unavailable:
        return CapabilityRequest(
            status="approval_required",
            requested=normalized,
            unavailable=unavailable,
            approval_required=True,
            activation_allowed=False,
            reason="Requested capabilities are unavailable and require separate external authorization.",
        )

    return CapabilityRequest(
        status="already_available",
        requested=normalized,
        unavailable=(),
        approval_required=False,
        activation_allowed=False,
        reason="Capabilities are already available; this request does not activate or modify anything.",
    )
