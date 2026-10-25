from core.capability_manifest import CapabilityManifest
from core.real_world_validation_contract import create_validation_request_spec


def test_corroborated_signal_without_capability_is_blocked():
    result = create_validation_request_spec(
        {"status": "corroborated_signal"},
        CapabilityManifest(),
    )

    assert result.status == "blocked"
    assert result.permitted_actions == ()
    assert "real_world_user_interaction" in result.blockers[0]


def test_non_corroborated_signal_is_not_ready():
    result = create_validation_request_spec(
        {"status": "mixed_signal"},
        CapabilityManifest(),
    )

    assert result.status == "not_ready"
    assert result.permitted_actions == ()


def test_future_enabled_capability_only_describes_request_action():
    result = create_validation_request_spec(
        {"status": "corroborated_signal"},
        CapabilityManifest(real_world_user_interaction=True),
    )

    assert result.status == "ready"
    assert result.permitted_actions == ("request_user_feedback",)
    assert "collect credentials" in " ".join(result.constraints).lower()
