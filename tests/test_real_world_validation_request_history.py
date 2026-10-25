from core.real_world_validation_request_history import (
    MAX_REAL_WORLD_VALIDATION_REQUEST_HISTORY,
    record_real_world_validation_request,
    real_world_validation_request_history,
)


def _packet(index: int) -> dict:
    return {
        "status": "blocked",
        "action": None,
        "purpose": f"purpose-{index}",
        "required_capabilities": ["real_world_user_interaction"],
        "constraints": ["no-side-effects"],
        "blockers": [f"blocked-{index}"],
        "side_effects_allowed": False,
        "execution_status": "not_executed",
        "request_fingerprint": f"fingerprint-{index}",
    }


def test_validation_request_history_is_bounded():
    build_plan = {}
    for index in range(MAX_REAL_WORLD_VALIDATION_REQUEST_HISTORY + 5):
        record_real_world_validation_request(build_plan, _packet(index))

    history = real_world_validation_request_history(build_plan)

    assert len(history) == MAX_REAL_WORLD_VALIDATION_REQUEST_HISTORY
    assert history[0]["request_fingerprint"] == "fingerprint-5"
    assert history[-1]["request_fingerprint"] == (
        f"fingerprint-{MAX_REAL_WORLD_VALIDATION_REQUEST_HISTORY + 4}"
    )


def test_validation_request_history_records_integrity_result():
    build_plan = {}
    entry = record_real_world_validation_request(
        build_plan,
        _packet(1),
        integrity={"valid": False, "issues": ["capability mismatch"]},
    )

    assert entry["integrity_valid"] is False
    assert entry["integrity_issues"] == ["capability mismatch"]


def test_validation_request_history_preserves_non_execution_boundary():
    build_plan = {}
    entry = record_real_world_validation_request(build_plan, _packet(1))

    assert entry["purpose"] == "purpose-1"
    assert entry["constraints"] == ["no-side-effects"]
    assert entry["execution_status"] == "not_executed"
    assert entry["side_effects_allowed"] is False
    assert real_world_validation_request_history(build_plan)[0] == entry


def test_validation_request_history_is_safe_for_invalid_state():
    assert real_world_validation_request_history({}) == []
    assert real_world_validation_request_history(
        {"real_world_validation_request_history": "bad"}
    ) == []

    build_plan = {"real_world_validation_request_history": "bad"}
    entry = record_real_world_validation_request(build_plan, _packet(1))

    assert entry["status"] == "blocked"
    assert len(build_plan["real_world_validation_request_history"]) == 1
