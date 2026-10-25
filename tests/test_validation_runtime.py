from core.brain import BrainDecision
from core.runtime import RuntimeState
from core.opportunity_evaluator import OpportunitySelection, OpportunityValidation
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_runtime_generates_validation_plan_after_validated_selection(tmp_path, monkeypatch):
    monkeypatch.setattr('database.connection.DATABASE_PATH', tmp_path / 'test.db')
    initialize_database()
    monkeypatch.setattr(
        'core.runtime.select_best_opportunity',
        lambda evidence, goal: OpportunitySelection(
            'selected', 'Simple SaaS', 'https://example.com/saas', 12,
            ('explicit monetization',), len(evidence)
        ),
    )
    monkeypatch.setattr(
        'core.runtime.check_selected_opportunity',
        lambda selected, evidence: OpportunityValidation(
            'validated', selected['title'], selected['url'],
            ('monetization is explicit', 'startup signal is compatible with a zero-cost start', 'evidence confidence is medium'),
            ('monetization', 'zero-cost-compatible startup', 'medium confidence'),
            len(evidence),
        ),
    )
    runtime = RuntimeState()
    memory = WorkingMemory(
        current_goal='software income',
        candidate_urls=['https://example.com/saas'],
        candidate_index=0,
        opportunity_evidence=[
            {
                'url': 'https://other.example.org/source',
                'title': 'Simple SaaS',
                'monetization': 'subscription',
                'startup_cost': 'explicitly mentions a free/no-upfront option',
                'capital_fit': 'promising for zero start',
                'confidence': 'medium',
                'quality_score': 3,
                'relevance_score': 4,
            }
        ],
    )
    decision = BrainDecision(
        thought='Inspect final candidate',
        goal='software income',
        plan=['Inspect final candidate'],
        action='http_get',
        reason='Inspect source',
        action_input={'url': 'https://example.com/saas'},
    )
    result = '[BEGIN UNTRUSTED WEB CONTENT]<title>Simple SaaS</title>subscription free plan beginner software[END UNTRUSTED WEB CONTENT]'

    updated = runtime.update_adaptive_plan(
        memory.to_dict(), decision, runtime.authorize(decision), result
    )

    assert updated.selected_opportunity is not None
    assert updated.selected_opportunity['validation']['status'] == 'validated'
    assert updated.validation_plan is not None
    assert updated.validation_plan['cost_ceiling'] == '₹0 owner funding'
    assert 'Execute the zero-cost validation plan' in (updated.current_task or '')
