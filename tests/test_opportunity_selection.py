from core.opportunity_evaluator import select_best_opportunity


def test_selection_requires_multiple_evidence_sources():
    selection = select_best_opportunity(
        [{
            "url": "https://example.com/saas",
            "title": "Simple SaaS",
            "monetization": "subscription",
            "startup_cost": "explicitly mentions a free/no-upfront option",
            "difficulty": "beginner",
            "capital_fit": "promising for ₹0 start, subject to actual requirements",
            "confidence": "medium",
        }],
        "software income",
    )

    assert selection.status == "insufficient_evidence"
    assert selection.title is None
    assert selection.evidence_count == 1


def test_selection_chooses_positive_best_candidate():
    evidence = [
        {
            "url": "https://example.com/saas",
            "title": "Simple SaaS",
            "monetization": "subscription",
            "startup_cost": "explicitly mentions a free/no-upfront option",
            "difficulty": "beginner",
            "capital_fit": "promising for ₹0 start, subject to actual requirements",
            "confidence": "medium",
        },
        {
            "url": "https://service.example.org/service",
            "title": "Technical Service",
            "monetization": "services",
            "startup_cost": "not stated",
            "difficulty": "technical",
            "capital_fit": "unknown",
            "confidence": "medium",
        },
    ]

    selection = select_best_opportunity(evidence, "software income")

    assert selection.status == "selected"
    assert selection.title == "Simple SaaS"
    assert selection.url == "https://example.com/saas"
    assert selection.score is not None and selection.score > 0
    assert selection.evidence_count == 2


def test_selection_refuses_when_all_evidence_is_neutral():
    evidence = [
        {
            "url": "https://example.com/one",
            "title": "Unknown One",
            "monetization": "unknown",
            "startup_cost": "not stated",
            "difficulty": "not stated",
            "capital_fit": "unknown",
            "confidence": "low",
        },
        {
            "url": "https://second.example.org/two",
            "title": "Unknown Two",
            "monetization": "unknown",
            "startup_cost": "not stated",
            "difficulty": "not stated",
            "capital_fit": "unknown",
            "confidence": "low",
        },
    ]

    selection = select_best_opportunity(evidence, "software income")

    assert selection.status == "insufficient_evidence"
    assert selection.title is None
