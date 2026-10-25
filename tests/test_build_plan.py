from core.build_plan import compile_build_plan


def test_compile_build_plan_requires_spec():
    assert compile_build_plan(None) is None


def test_compile_build_plan_is_minimal_and_testable():
    spec = {
        "title": "Simple SaaS",
        "mvp_scope": ["one workflow", "one metric"],
        "known_constraints": ["No owner capital."],
    }

    plan = compile_build_plan(spec)

    assert plan is not None
    assert plan.title == "Simple SaaS"
    assert "one workflow" in plan.implementation_steps[1]
    assert "Automated tests" in plan.deliverables[1]
    assert any("zero-cost" in item for item in plan.acceptance_criteria)
    assert "No owner capital." in plan.constraints
