from core.brain import BrainDecision
from core.runtime import RuntimeState


def test_runtime_capability_gate_blocks_sandbox_when_disabled():
    runtime = RuntimeState()
    runtime.capabilities = runtime.capabilities.__class__(sandbox_mutation=False)
    runtime.capability_lock = runtime.capability_lock.from_manifest(
        runtime.capabilities
    )

    decision = BrainDecision(
        "write prototype",
        "test",
        [],
        "sandbox_write",
        "test",
        {"path": "demo/app.py", "content": "print('x')"},
    )

    result = runtime.authorize(decision)

    assert result.allowed is False
    assert "sandbox_mutation" in result.reason


def test_runtime_capability_gate_allows_web_search_by_default():
    runtime = RuntimeState()
    decision = BrainDecision(
        "search",
        "test",
        [],
        "web_search",
        "test",
        {"query": "example"},
    )

    result = runtime.authorize(decision)

    assert result.allowed is True


def test_runtime_security_policy_still_wins_for_unknown_action():
    runtime = RuntimeState()
    decision = BrainDecision(
        "unknown",
        "test",
        [],
        "payments",
        "test",
        {},
    )

    result = runtime.authorize(decision)

    assert result.allowed is False
    assert "security policy" in result.reason
