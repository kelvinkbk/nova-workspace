from core.real_world_validation_approval_binding_history import (
    MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY,
    record_real_world_validation_approval_binding,
    real_world_validation_approval_binding_history,
)


def test_binding_history_is_bounded():
    build_plan = {}
    for index in range(MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY + 5):
        record_real_world_validation_approval_binding(
            build_plan,
            {
                "valid": index % 2 == 0,
                "issues": [f"issue-{index}"],
                "enforcement_status": "validated" if index % 2 == 0 else "blocked",
                "enforcement_reason": "passed" if index % 2 == 0 else "failed",
            },
        )

    history = real_world_validation_approval_binding_history(build_plan)

    assert len(history) == MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY
    assert history[0]["issues"] == ["issue-5"]
    assert history[-1]["issues"] == [
        f"issue-{MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY + 4}"
    ]
    assert history[-1]["enforcement_status"] == "validated" if (MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY + 4) % 2 == 0 else "blocked"
    assert history[-1]["enforcement_reason"] == "passed" if (MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY + 4) % 2 == 0 else "failed"


def test_binding_history_records_valid_decision():
    build_plan = {}
    entry = record_real_world_validation_approval_binding(
        build_plan,
        {"valid": True, "issues": []},
    )

    assert entry["valid"] is True
    assert entry["issues"] == []
    assert entry["enforcement_status"] == ""
    assert entry["enforcement_reason"] == ""
    assert real_world_validation_approval_binding_history(build_plan)[0] == entry


def test_binding_history_records_rejection_issues():
    build_plan = {}
    entry = record_real_world_validation_approval_binding(
        build_plan,
        {"valid": False, "issues": ["fingerprint mismatch"]},
    )

    assert entry["valid"] is False
    assert entry["issues"] == ["fingerprint mismatch"]
    assert entry["enforcement_status"] == ""
    assert entry["enforcement_reason"] == ""


def test_binding_history_is_safe_for_invalid_state():
    assert real_world_validation_approval_binding_history({}) == []
    assert real_world_validation_approval_binding_history(
        {"real_world_validation_approval_binding_history": "bad"}
    ) == []

    build_plan = {
        "real_world_validation_approval_binding_history": "bad",
    }
    entry = record_real_world_validation_approval_binding(
        build_plan,
        {"valid": False, "issues": ["invalid state"]},
    )

    assert entry["valid"] is False
    assert len(build_plan["real_world_validation_approval_binding_history"]) == 1
