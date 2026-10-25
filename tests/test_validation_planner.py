from core.validation_planner import build_validation_plan


def test_validation_plan_requires_selection():
    assert build_validation_plan(None, []) is None


def test_validation_plan_is_zero_cost_and_measurable():
    selected = {
        "status": "selected",
        "title": "Simple SaaS",
        "url": "https://example.com/saas",
    }
    evidence = [
        {
            "monetization": "subscription",
            "startup_cost": "explicitly mentions a free/no-upfront option",
            "capital_fit": "promising for zero start",
        }
    ]

    plan = build_validation_plan(selected, evidence)

    assert plan is not None
    assert plan.cost_ceiling == "₹0 owner funding"
    assert len(plan.steps) >= 4
    assert any("demand" in item.lower() for item in plan.success_criteria)
    assert plan.blockers == ()


def test_validation_plan_records_missing_signals():
    selected = {
        "status": "selected",
        "title": "Paid Tool",
        "url": "https://example.com/tool",
    }
    plan = build_validation_plan(selected, [{"monetization": "subscription"}])

    assert plan is not None
    assert len(plan.blockers) == 1
    assert "zero-cost" in plan.blockers[0].lower()
