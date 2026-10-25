from core.opportunity_evaluator import (
    compare_opportunity_evidence,
    summarize_evidence_comparison,
)


def test_comparison_prefers_explicit_zero_cost_monetizable_candidate():
    evidence = [
        {
            "url": "https://example.com/paid",
            "title": "Technical SaaS",
            "monetization": "subscription",
            "startup_cost": "price signal found: $49",
            "difficulty": "technical",
            "capital_fit": "unknown; inspect the actual pricing/requirements",
            "confidence": "medium",
        },
        {
            "url": "https://example.com/free",
            "title": "Beginner Automation Tool",
            "monetization": "subscription",
            "startup_cost": "explicitly mentions a free/no-upfront option",
            "difficulty": "beginner",
            "capital_fit": "promising for ₹0 start, subject to actual requirements",
            "confidence": "medium",
        },
    ]

    ranked = compare_opportunity_evidence(evidence, "software income")

    assert ranked[0].title == "Beginner Automation Tool"
    assert ranked[0].score > ranked[1].score


def test_comparison_does_not_treat_unknown_fields_as_positive_facts():
    evidence = [
        {
            "url": "https://example.com/unknown",
            "title": "Unknown Source",
            "monetization": "unknown",
            "startup_cost": "not stated",
            "difficulty": "not stated",
            "capital_fit": "unknown",
            "confidence": "low",
        }
    ]

    ranked = compare_opportunity_evidence(evidence, "software income")

    assert ranked[0].score == 0
    assert "insufficient explicit evidence" in ranked[0].reasons[0]


def test_runtime_sets_selection_task_after_final_candidate(tmp_path, monkeypatch):
    from core.brain import BrainDecision
    from core.runtime import RuntimeState
    from database.schema import initialize_database
    from memory.working import WorkingMemory
    from security.policy import PolicyDecision

    monkeypatch.setattr('database.connection.DATABASE_PATH', tmp_path / 'runtime.db')
    initialize_database()
    runtime = RuntimeState()
    memory = WorkingMemory(
        current_goal='software income',
        candidate_urls=['https://example.com/one', 'https://example.org/two'],
        candidate_index=1,
        opportunity_evidence=[
            {
                'url': 'https://example.com/one',
                'title': 'Simple SaaS',
                'monetization': 'subscription',
                'startup_cost': 'explicitly mentions a free/no-upfront option',
                'difficulty': 'beginner',
                'capital_fit': 'promising for ₹0 start, subject to actual requirements',
                'confidence': 'medium',
            }
        ],
    )
    decision = BrainDecision(
        thought='Inspect second source', goal='software income', plan=['Inspect'],
        action='http_get', reason='Inspect source',
        action_input={'url': 'https://example.org/two'},
    )
    result = '[BEGIN UNTRUSTED WEB CONTENT]<title>Technical SaaS</title>subscription $49 technical[END UNTRUSTED WEB CONTENT]'

    updated = runtime.update_adaptive_plan(
        memory.to_dict(),
        decision,
        PolicyDecision('http_get', True, 'allowed'),
        result,
    )

    assert updated.current_task == 'Execute the zero-cost validation plan for: Simple SaaS'
    assert updated.validation_plan is not None
    assert updated.selected_opportunity['status'] == 'selected'
    assert updated.selected_opportunity['title'] == 'Simple SaaS'
    assert updated.selected_opportunity['validation']['status'] == 'validated'
    assert any(note.startswith('Evidence comparison:') for note in updated.notes)
    assert len(updated.opportunity_evidence) == 2


def test_comparison_summary_names_strongest_candidate():
    evidence = [
        {
            "url": "https://example.com/one",
            "title": "Simple Digital Product",
            "monetization": "digital product",
            "startup_cost": "explicitly mentions a free/no-upfront option",
            "difficulty": "simple",
            "capital_fit": "promising for ₹0 start, subject to actual requirements",
            "confidence": "medium",
        },
        {
            "url": "https://example.com/two",
            "title": "Technical Service",
            "monetization": "services",
            "startup_cost": "not stated",
            "difficulty": "technical",
            "capital_fit": "unknown",
            "confidence": "medium",
        },
    ]

    summary = summarize_evidence_comparison(evidence, "digital product")

    assert "strongest inspected candidate is Simple Digital Product" in summary
    assert "score=" in summary
