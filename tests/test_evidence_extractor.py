from core.evidence_extractor import extract_opportunity_evidence


def test_extracts_capital_and_monetization():
    evidence = extract_opportunity_evidence(
        '<title>Simple SaaS Tool</title> Build a subscription product with a free plan and no upfront cost. Beginner friendly.',
        'https://example.com/saas',
    )
    assert evidence.monetization in {'subscription', 'saas'}
    assert 'free/no-upfront' in evidence.startup_cost
    assert evidence.difficulty == 'beginner'


def test_unknown_fields_are_not_invented():
    evidence = extract_opportunity_evidence('No business details here.', 'https://example.com/source')
    assert evidence.monetization == 'unknown'
    assert evidence.startup_cost == 'not stated'
    assert evidence.difficulty == 'not stated'
    assert evidence.confidence == 'low'
