from core.experiment_evaluator import evaluate_experiment_result


def test_failed_experiment_is_blocked():
    result = evaluate_experiment_result("Search failed: timeout")

    assert result.status == "blocked"
    assert result.signal_strength == "none"


def test_search_with_demand_signals_produces_moderate_evidence():
    text = """[BEGIN UNTRUSTED WEB SEARCH RESULTS]
1. Customers and pricing
   URL: https://example.com/1
2. Market demand and paid subscription revenue
   URL: https://example.com/2
[END UNTRUSTED WEB SEARCH RESULTS]"""

    result = evaluate_experiment_result(text)

    assert result.status == "evidence_found"
    assert result.signal_strength == "moderate"


def test_search_results_do_not_claim_real_demand():
    text = """[BEGIN UNTRUSTED WEB SEARCH RESULTS]
1. Example software
   URL: https://example.com/1
[END UNTRUSTED WEB SEARCH RESULTS]"""

    result = evaluate_experiment_result(text)

    assert result.status == "inconclusive"
    assert result.signal_strength == "weak"
    assert result.blockers


def test_unknown_result_is_inconclusive():
    result = evaluate_experiment_result("some unrelated output")

    assert result.status == "inconclusive"
