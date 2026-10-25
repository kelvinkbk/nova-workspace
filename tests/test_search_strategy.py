from core.search_strategy import build_search_queries, next_search_query


def test_search_strategy_uses_evidence_oriented_terms():
    queries = build_search_queries("Become financially self-sustaining through software")
    assert len(queries) == 5
    assert "monetization" in queries[0]
    assert "free" in queries[0]
    assert "pricing" in queries[1]


def test_search_strategy_changes_query_after_previous_search():
    queries = build_search_queries("software income")
    selected = next_search_query("software income", [queries[0]])

    assert selected == queries[1]
    assert selected != queries[0]


def test_search_strategy_falls_back_when_all_queries_seen():
    queries = build_search_queries("software income")
    selected = next_search_query("software income", queries)

    assert selected == queries[0]
