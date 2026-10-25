from core.build_decision import decide_first_build


def _selected():
    return {
        "status": "selected",
        "title": "Simple SaaS",
        "url": "https://example.com/saas",
        "validation": {"status": "validated"},
    }


def _evidence():
    return [
        {
            "monetization": "subscription",
            "startup_cost": "explicitly mentions a free/no-upfront option",
            "capital_fit": "promising for zero start",
        }
    ]


def _plan(observations, status="blocked"):
    return {
        "title": "Simple SaaS",
        "status": status,
        "step_index": 4,
        "observations": [{"step_index": i, "action": "web_search", "result": text}
                         for i, text in enumerate(observations)],
    }


def test_build_decision_requires_real_demand_signals():
    result = decide_first_build(
        _selected(),
        _plan(["pricing found", "free plan found", "technical details", "market overview"]),
        _evidence(),
    )
    assert result.status == "do_not_build_yet"


def test_build_decision_allows_minimal_build_with_demand():
    result = decide_first_build(
        _selected(),
        _plan([
            "customers report this problem and active demand",
            "pricing and paying customers are visible",
            "users need a simple workflow",
            "free distribution is possible",
        ]),
        _evidence(),
    )
    assert result.status == "build_minimal"
    assert result.scope
    assert result.next_action.startswith("Define and implement")


def test_build_decision_is_blocked_without_validation():
    result = decide_first_build(None, None, [])
    assert result.status == "blocked"
