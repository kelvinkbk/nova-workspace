from core.experiment_decision import decide_experiment_outcome


def _result(status, urls):
    body = "\n".join(f"URL: {url}" for url in urls)
    return {
        "status": "completed",
        "result": f"[BEGIN UNTRUSTED WEB SEARCH RESULTS]\n{body}\n[END UNTRUSTED WEB SEARCH RESULTS]",
        "evaluation": {"status": status},
    }


def test_two_positive_experiments_from_two_domains_are_corroborated():
    result = decide_experiment_outcome(
        _result("evidence_found", ["https://a.example.com/one"]),
        _result("evidence_found", ["https://b.example.com/two"]),
    )

    assert result.status == "corroborated_signal"
    assert result.confidence == "moderate"
    assert len(result.source_domains) == 2


def test_positive_results_from_one_domain_are_not_corroborated():
    result = decide_experiment_outcome(
        _result("evidence_found", ["https://example.com/one"]),
        _result("evidence_found", ["https://example.com/two"]),
    )

    assert result.status == "mixed_signal"
    assert result.confidence == "low"


def test_one_positive_one_inconclusive_is_mixed():
    result = decide_experiment_outcome(
        _result("evidence_found", ["https://a.example.com/one"]),
        _result("inconclusive", ["https://b.example.com/two"]),
    )

    assert result.status == "mixed_signal"


def test_failed_experiment_blocks():
    result = decide_experiment_outcome(
        _result("blocked", []),
        _result("evidence_found", ["https://b.example.com/two"]),
    )

    assert result.status == "blocked"
    assert result.confidence == "none"
