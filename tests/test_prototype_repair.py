from core.prototype_repair import build_repair_plan


def test_repair_plan_for_syntax_error_is_bounded():
    result = build_repair_plan({"failure_type": "syntax_error"})

    assert result.status == "ready"
    assert result.failure_type == "syntax_error"
    assert any("syntax" in step.lower() for step in result.steps)
    assert "No package installation or external side effects." in result.constraints


def test_repair_plan_for_missing_dependency_avoids_installation():
    result = build_repair_plan({"failure_type": "missing_dependency_or_import"})

    assert any("standard library" in step.lower() for step in result.steps)
    assert any("do not install packages" in step.lower() for step in result.steps)


def test_repair_plan_unknown_failure_stays_generic():
    result = build_repair_plan({"failure_type": "something_new"})

    assert result.status == "ready"
    assert any("deterministic root cause" in step.lower() for step in result.steps)
    assert any("sandbox only" in item.lower() for item in result.constraints)
