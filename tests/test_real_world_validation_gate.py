from core.real_world_validation_gate import create_real_world_validation_gate


def test_corroborated_signal_is_blocked_without_real_world_interaction():
    result = create_real_world_validation_gate(
        {"status": "corroborated_signal"},
        ["web_search", "http_get"],
    )

    assert result.status == "blocked"
    assert "real-world user interaction" in result.blockers[0]
    assert "do not claim demand" in result.next_action.lower()


def test_non_corroborated_signal_is_not_ready():
    result = create_real_world_validation_gate(
        {"status": "mixed_signal"},
        ["web_search"],
    )

    assert result.status == "not_ready"
    assert result.blockers


def test_empty_capabilities_are_recorded():
    result = create_real_world_validation_gate({"status": "corroborated_signal"})

    assert result.status == "blocked"
    assert "real_world_user_interaction" not in result.available_capabilities
    assert "read_only_research" in result.available_capabilities
