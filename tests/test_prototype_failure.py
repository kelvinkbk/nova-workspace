from core.prototype_failure import diagnose_project_test_failure


def test_diagnoses_timeout():
    result = diagnose_project_test_failure(
        "Sandbox project tests timed out after 5 seconds."
    )

    assert result.failure_type == "timeout"
    assert result.status == "failed"


def test_diagnoses_import_error():
    result = diagnose_project_test_failure(
        "Sandbox project tests failed (exit code 1):\nModuleNotFoundError: No module named 'x'"
    )

    assert result.failure_type == "missing_dependency_or_import"
    assert "exit code 1" in result.summary


def test_diagnoses_syntax_error():
    result = diagnose_project_test_failure(
        "Sandbox project tests failed (exit code 1): SyntaxError: invalid syntax"
    )

    assert result.failure_type == "syntax_error"


def test_diagnoses_assertion_failure():
    result = diagnose_project_test_failure(
        "Sandbox project tests failed (exit code 1): AssertionError"
    )

    assert result.failure_type == "assertion_or_test_failure"
