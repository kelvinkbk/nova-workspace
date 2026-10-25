from core.real_world_validation_request import build_real_world_validation_request


def test_blocked_spec_creates_non_executing_packet():
    result = build_real_world_validation_request(
        {
            "status": "blocked",
            "purpose": "Validate real user demand.",
            "required_capabilities": ["real_world_user_interaction"],
            "blockers": ["Capability unavailable."],
            "constraints": ["Do not collect credentials."],
        }
    )

    assert result.status == "blocked"
    assert result.action is None
    assert result.execution_status == "not_executed"
    assert result.side_effects_allowed is False
    assert result.request_fingerprint


def test_ready_spec_is_prepared_but_never_executable():
    result = build_real_world_validation_request(
        {
            "status": "ready",
            "purpose": "Validate real user demand using one interaction.",
            "required_capabilities": ["real_world_user_interaction"],
            "constraints": ["Do not collect credentials."],
            "blockers": [],
        }
    )

    assert result.status == "prepared"
    assert result.action == "request_user_feedback"
    assert result.execution_status == "not_executed"
    assert result.side_effects_allowed is False


def test_same_spec_has_stable_fingerprint():
    spec = {
        "status": "ready",
        "purpose": "Validate demand.",
        "required_capabilities": ["real_world_user_interaction"],
        "constraints": ["Do not collect credentials."],
        "blockers": [],
    }

    first = build_real_world_validation_request(spec)
    second = build_real_world_validation_request(dict(spec))

    assert first.request_fingerprint == second.request_fingerprint


def test_changed_request_changes_fingerprint():
    base = {
        "status": "ready",
        "purpose": "Validate demand.",
        "required_capabilities": ["real_world_user_interaction"],
        "constraints": ["Do not collect credentials."],
        "blockers": [],
    }

    changed = dict(base, purpose="Validate demand with revised wording.")

    first = build_real_world_validation_request(base)
    second = build_real_world_validation_request(changed)

    assert first.request_fingerprint != second.request_fingerprint


def test_malformed_input_fails_closed():
    result = build_real_world_validation_request(None)

    assert result.status == "blocked"
    assert result.action is None
    assert result.side_effects_allowed is False
    assert result.execution_status == "not_executed"
