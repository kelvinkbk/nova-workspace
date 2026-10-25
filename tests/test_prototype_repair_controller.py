from core.prototype_repair_controller import (
    choose_repair_action,
    validate_repair_write,
)


def test_repair_controller_allows_one_bounded_attempt():
    result = choose_repair_action(
        {
            "repair_attempts": 0,
            "prototype_failure": {"failure_type": "syntax_error"},
            "prototype_repair_plan": {"status": "ready"},
        }
    )

    assert result.status == "ready"
    assert result.action == "sandbox_write"
    assert result.max_attempts == 1


def test_repair_controller_blocks_after_one_attempt():
    result = choose_repair_action(
        {
            "repair_attempts": 1,
            "prototype_failure": {"failure_type": "syntax_error"},
            "prototype_repair_plan": {"status": "ready"},
        }
    )

    assert result.status == "blocked"
    assert result.action is None


def test_repair_controller_requires_diagnosis_and_plan():
    result = choose_repair_action({"repair_attempts": 0})

    assert result.status == "blocked"
    assert "diagnosis and repair plan" in result.reason


def test_validate_repair_write_allows_active_scaffold_file():
    result, error = validate_repair_write(
        {"scaffold_path": "builds/demo"},
        {"path": "builds/demo/app.py", "content": "print('fixed')"},
    )

    assert error is None
    assert result["path"] == "builds/demo/app.py"


def test_validate_repair_write_blocks_other_sandbox_paths():
    result, error = validate_repair_write(
        {"scaffold_path": "builds/demo"},
        {"path": "builds/other/app.py", "content": "print('bad')"},
    )

    assert result is None
    assert "active scaffold" in error


def test_validate_repair_write_blocks_unsupported_files():
    result, error = validate_repair_write(
        {"scaffold_path": "builds/demo"},
        {"path": "builds/demo/README.md", "content": "bad"},
    )

    assert result is None
    assert "only app.py or test_app.py" in error
