from core.opportunity_evaluator import select_best_opportunity


def _item(url):
    return {
        "url": url,
        "title": "Simple SaaS",
        "monetization": "subscription",
        "startup_cost": "explicitly mentions a free/no-upfront option",
        "difficulty": "beginner",
        "capital_fit": "promising for ₹0 start, subject to actual requirements",
        "confidence": "medium",
    }


def test_selection_rejects_same_domain_evidence():
    result = select_best_opportunity(
        [_item("https://example.com/a"), _item("https://example.com/b")],
        "software income",
    )

    assert result.status == "insufficient_source_diversity"


def test_selection_accepts_two_distinct_domains():
    result = select_best_opportunity(
        [_item("https://example.com/a"), _item("https://example.org/b")],
        "software income",
    )

    assert result.status == "selected"
    assert result.evidence_count == 2
