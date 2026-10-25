from core.capability_gate import evaluate_capability
from core.capability_manifest import CapabilityManifest


def test_user_feedback_requires_real_world_interaction_capability():
    result = evaluate_capability(
        "request_user_feedback",
        CapabilityManifest(),
    )

    assert result.allowed is False
    assert result.capability == "real_world_user_interaction"


def test_user_feedback_becomes_capability_allowed_only_when_manifest_allows_it():
    result = evaluate_capability(
        "request_user_feedback",
        CapabilityManifest(real_world_user_interaction=True),
    )

    assert result.allowed is True
    assert result.capability == "real_world_user_interaction"


def test_internal_action_without_mapping_remains_internal():
    result = evaluate_capability(
        "record_observation",
        CapabilityManifest(),
    )

    assert result.allowed is True
    assert result.capability is None
