from core.evidence_extractor import extract_opportunity_evidence
from core.opportunity_evaluator import compare_opportunity_evidence


def test_quality_classifies_official_source_as_high():
    evidence = extract_opportunity_evidence(
        "Pricing: free plan. Subscription available. Beginner.",
        "https://docs.example.gov.in/pricing",
    )

    assert evidence.source_type == "official_or_educational"
    assert evidence.source_quality == "high"
    assert evidence.quality_score == 5


def test_quality_classifies_community_source_as_medium():
    evidence = extract_opportunity_evidence(
        "Case study: subscription revenue and beginner setup.",
        "https://www.reddit.com/r/startups/example",
    )

    assert evidence.source_type == "community"
    assert evidence.source_quality == "medium"
    assert evidence.quality_score == 3


def test_quality_breaks_ties_in_favor_of_stronger_source():
    evidence = [
        {
            "url": "https://www.example.com/a",
            "title": "Simple SaaS",
            "monetization": "subscription",
            "startup_cost": "not stated",
            "difficulty": "beginner",
            "capital_fit": "unknown",
            "confidence": "medium",
            "source_quality": "low",
            "quality_score": 1,
        },
        {
            "url": "https://www.docs.example.com/b",
            "title": "Simple SaaS",
            "monetization": "subscription",
            "startup_cost": "not stated",
            "difficulty": "beginner",
            "capital_fit": "unknown",
            "confidence": "medium",
            "source_quality": "high",
            "quality_score": 5,
        },
    ]

    ranked = compare_opportunity_evidence(evidence, "software income")

    assert ranked[0].url == "https://www.docs.example.com/b"
    assert any("source quality: high" in reason for reason in ranked[0].reasons)
