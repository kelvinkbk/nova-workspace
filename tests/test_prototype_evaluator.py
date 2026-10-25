from core.prototype_evaluator import evaluate_prototype


def valid_plan() -> dict:
    return {
        "title": "Example",
        "objective": "Build a minimal prototype.",
        "deliverables": ["README.md", "app.py", "test_app.py"],
        "implementation_steps": ["Create the smallest implementation."],
        "test_strategy": ["Run deterministic tests."],
        "acceptance_criteria": ["End-to-end reproducible."],
        "constraints": ["Rs 0 owner funding"],
    }


def test_evaluate_prototype_verifies_complete_pass():
    result = evaluate_prototype(
        valid_plan(),
        "Sandbox execution succeeded: prototype-ready",
        "Sandbox project tests passed: 1 passed",
    )

    assert result.status == "verified"
    assert all(result.checks.values())
    assert result.blockers == []


def test_evaluate_prototype_requires_smoke_and_project_tests():
    result = evaluate_prototype(valid_plan())

    assert result.status == "review_required"
    assert "Bounded smoke test has not passed." in result.blockers
    assert "Generated project test suite has not passed." in result.blockers


def test_evaluate_prototype_requires_zero_cost_constraint():
    plan = valid_plan()
    plan["constraints"] = []

    result = evaluate_prototype(
        plan,
        "Sandbox execution succeeded: prototype-ready",
        "Sandbox project tests passed: 1 passed",
    )

    assert result.status == "review_required"
    assert "Zero-cost owner-funding constraint is not explicit." in result.blockers
