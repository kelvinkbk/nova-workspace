from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class CapabilityIntegrityDecision:
    intact: bool
    fingerprint: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "intact": self.intact,
            "fingerprint": self.fingerprint,
            "reason": self.reason,
        }


def fingerprint_manifest(manifest) -> str:
    payload = json.dumps(
        manifest.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class CapabilityIntegrityLock:
    fingerprint: str

    @classmethod
    def from_manifest(cls, manifest):
        return cls(fingerprint=fingerprint_manifest(manifest))

    def verify(self, manifest) -> CapabilityIntegrityDecision:
        current = fingerprint_manifest(manifest)
        if current == self.fingerprint:
            return CapabilityIntegrityDecision(
                intact=True,
                fingerprint=current,
                reason="Capability manifest integrity verified.",
            )
        return CapabilityIntegrityDecision(
            intact=False,
            fingerprint=current,
            reason="Capability manifest changed after the runtime integrity lock was created.",
        )
