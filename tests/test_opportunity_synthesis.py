from core.opportunity_synthesis import synthesize_opportunity_evidence


def test_synthesis_combines_same_opportunity_sources():
    evidence = [
        {
            "url": "https://example.com/product",
            "title": "Simple SaaS",
            "monetization": "subscription",
            "startup_cost": "not stated",
            "difficulty": "beginner",
            "capital_fit": "unknown",
            "confidence": "medium",
            "quality_score": 5,
            "relevance_score": 5,
        },
        {
            "url": "https://example.org/simple-saas-case-study",
            "title": "Simple SaaS",
            "monetization": "unknown",
            "startup_cost": "explicitly mentions a free/no-upfront option",
            "difficulty": "not stated",
            "capital_fit": "promising for zero start",
            "confidence": "medium",
            "quality_score": 3,
            "relevance_score": 4,
        },
    ]

    result = synthesize_opportunity_evidence(evidence)

    assert len(result) == 1
    item = result[0]
    assert item.source_count == 2
    assert item.monetization == "subscription"
    assert "free/no-upfront" in item.startup_cost
    assert set(item.urls) == {
        "https://example.com/product",
        "https://example.org/simple-saas-case-study",
    }
    assert "monetization" in item.field_sources
    assert "startup_cost" in item.field_sources


def test_synthesis_keeps_different_titles_separate():
    evidence = [
        {
            "url": "https://example.com/a",
            "title": "Simple SaaS",
            "monetization": "subscription",
            "startup_cost": "not stated",
            "difficulty": "beginner",
            "capital_fit": "unknown",
            "confidence": "medium",
            "quality_score": 3,
            "relevance_score": 3,
        },
        {
            "url": "https://example.org/b",
            "title": "Developer Analytics Tool",
            "monetization": "services",
            "startup_cost": "not stated",
            "difficulty": "technical",
            "capital_fit": "unknown",
            "confidence": "medium",
            "quality_score": 3,
            "relevance_score": 3,
        },
    ]

    result = synthesize_opportunity_evidence(evidence)

    assert len(result) == 2


def test_synthesis_uses_html_title_when_title_missing():
    from core.evidence_extractor import extract_opportunity_evidence

    content = """
    <html>
      <head><title>Simple SaaS Pricing</title></head>
      <body>Subscription pricing with a free plan for beginners.</body>
    </html>
    """
    evidence = extract_opportunity_evidence(
        content,
        "https://pricing.example.com/simple-saas",
        goal="software monetization",
    )

    assert evidence.title == "Simple SaaS Pricing"
