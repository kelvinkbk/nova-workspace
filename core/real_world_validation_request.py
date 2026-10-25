import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class RealWorldValidationRequestPacket:
    status: str
    action: str | None
    purpose: str
    required_capabilities: tuple[str, ...]
    constraints: tuple[str, ...]
    blockers: tuple[str, ...]
    side_effects_allowed: bool
    execution_status: str
    request_fingerprint: str

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "action": self.action,
            "purpose": self.purpose,
            "required_capabilities": list(self.required_capabilities),
            "constraints": list(self.constraints),
            "blockers": list(self.blockers),
            "side_effects_allowed": self.side_effects_allowed,
            "execution_status": self.execution_status,
            "request_fingerprint": self.request_fingerprint,
        }


def build_real_world_validation_request(
    validation_request_spec: dict | None,
) -> RealWorldValidationRequestPacket:
    spec = validation_request_spec if isinstance(validation_request_spec, dict) else {}

    status = str(spec.get("status") or "blocked").strip().lower()
    purpose = str(spec.get("purpose") or "").strip()
    required = tuple(
        dict.fromkeys(
            str(item).strip()
            for item in (spec.get("required_capabilities") or [])
            if str(item).strip()
        )
    )
    constraints = tuple(
        dict.fromkeys(
            str(item).strip()
            for item in (spec.get("constraints") or [])
            if str(item).strip()
        )
    )
    blockers = tuple(
        dict.fromkeys(
            str(item).strip()
            for item in (spec.get("blockers") or [])
            if str(item).strip()
        )
    )

    prepared = status == "ready" and not blockers
    packet_status = "prepared" if prepared else status
    action = "request_user_feedback" if prepared else None
    execution_status = "not_executed"

    canonical = json.dumps(
        {
            "status": packet_status,
            "action": action,
            "purpose": purpose,
            "required_capabilities": list(required),
            "constraints": list(constraints),
            "blockers": list(blockers),
            "side_effects_allowed": False,
            "execution_status": execution_status,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    request_fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return RealWorldValidationRequestPacket(
        status=packet_status,
        action=action,
        purpose=purpose,
        required_capabilities=required,
        constraints=constraints,
        blockers=blockers,
        side_effects_allowed=False,
        execution_status=execution_status,
        request_fingerprint=request_fingerprint,
    )
