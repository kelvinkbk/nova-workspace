from core.capability_integrity import CapabilityIntegrityLock, fingerprint_manifest
from core.capability_manifest import CapabilityManifest


def test_manifest_fingerprint_is_deterministic():
    manifest = CapabilityManifest()

    assert fingerprint_manifest(manifest) == fingerprint_manifest(manifest)


def test_integrity_lock_accepts_unchanged_manifest():
    manifest = CapabilityManifest()
    lock = CapabilityIntegrityLock.from_manifest(manifest)

    result = lock.verify(manifest)

    assert result.intact is True
    assert result.fingerprint == lock.fingerprint


def test_integrity_lock_detects_changed_manifest():
    original = CapabilityManifest()
    lock = CapabilityIntegrityLock.from_manifest(original)
    changed = CapabilityManifest(sandbox_mutation=False)

    result = lock.verify(changed)

    assert result.intact is False
    assert "changed" in result.reason
