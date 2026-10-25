from core.opportunity_evaluator import check_selected_opportunity


def _evidence(url, title="Simple SaaS", monetization="subscription", startup_cost="explicitly mentions a free/no-upfront option", difficulty="beginner", capital_fit="promising for zero start", confidence="medium"):
    return {
        "url": url,
        "title": title,
        "monetization": monetization,
        "startup_cost": startup_cost,
        "difficulty": difficulty,
        "capital_fit": capital_fit,
        "confidence": confidence,
    }


def test_validation_requires_selected_candidate():
    result = check_selected_opportunity(None, [])

    assert result.status == "not_selected"
    assert result.title is None


def test_validation_accepts_explicit_requirements():
    selected = {
        "status": "selected",
        "title": "Simple SaaS",
        "url": "https://example.com/saas",
    }
    evidence = [
        _evidence("https://example.com/saas"),
        _evidence(
            "https://example.com/other",
            title="Other Tool",
            monetization="services",
            startup_cost="not stated",
            difficulty="technical",
            capital_fit="unknown",
            confidence="medium",
        ),
    ]

    result = check_selected_opportunity(selected, evidence)

    assert result.status == "validated"
    assert result.url == "https://example.com/saas"
    assert "monetization" in result.required_signals


def test_validation_requests_more_evidence_when_cost_is_unknown():
    selected = {
        "status": "selected",
        "title": "Paid Tool",
        "url": "https://example.com/tool",
    }
    evidence = [
        _evidence(
            "https://example.com/tool",
            title="Paid Tool",
            monetization="subscription",
            startup_cost="price signal found: $49",
            capital_fit="unknown",
            confidence="medium",
        ),
        _evidence(
            "https://example.com/source",
            title="General Source",
            monetization="unknown",
            startup_cost="not stated",
            difficulty="not stated",
            capital_fit="unknown",
            confidence="low",
        ),
    ]

    result = check_selected_opportunity(selected, evidence)

    assert result.status == "more_evidence"
    assert "zero-cost-compatible startup signal" in result.required_signals
