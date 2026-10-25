from core.brain import BrainDecision
from core.capability_integrity import CapabilityIntegrityLock
from core.capability_manifest import CapabilityManifest
from core.runtime import RuntimeState


def test_runtime_blocks_when_capability_manifest_is_tampered():
    runtime = RuntimeState()

    decision = BrainDecision(
        "search",
        "test",
        [],
        "web_search",
        "test",
        {"query": "example"},
    )

    runtime.capabilities = CapabilityManifest(read_only_research=False)
    result = runtime.authorize(decision)

    assert result.allowed is False
    assert "integrity check failed" in result.reason


def test_runtime_integrity_lock_matches_initial_manifest():
    runtime = RuntimeState()

    result = runtime.capability_lock.verify(runtime.capabilities)

    assert result.intact is True
