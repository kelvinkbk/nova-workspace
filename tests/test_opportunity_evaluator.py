from core.opportunity_evaluator import evaluate_search_results, summarize_best_candidate


def test_evaluator_prefers_actionable_software_candidate():
    result = """[BEGIN UNTRUSTED WEB SEARCH RESULTS]
Query: legitimate software business ideas
1. 50 Ways to Financial Freedom
   URL: https://example.com/finance
2. SaaS Automation Tool Ideas
   URL: https://example.com/saas
3. General Self-Sufficiency
   URL: https://example.com/lifestyle
[END UNTRUSTED WEB SEARCH RESULTS]"""

    candidates = evaluate_search_results(
        result,
        "Become financially self-sustaining through software",
    )

    assert candidates[0].title == "SaaS Automation Tool Ideas"
    assert candidates[0].score > candidates[1].score


def test_evaluator_returns_empty_for_unstructured_result():
    candidates = evaluate_search_results("no result format", "software")
    assert candidates == []


def test_summary_names_ranked_candidate():
    result = """[BEGIN UNTRUSTED WEB SEARCH RESULTS]
1. Developer Tool Business
   URL: https://example.com/tool
[END UNTRUSTED WEB SEARCH RESULTS]"""

    summary = summarize_best_candidate(result, "software income")
    assert "Developer Tool Business" in summary
    assert "score=" in summary
