from core.build_spec import build_minimal_spec


def _decision():
    return {
        "status": "build_minimal",
        "title": "Simple SaaS",
        "scope": ["one workflow", "one metric"],
    }


def _plan():
    return {
        "status": "blocked",
        "observations": [
            {"result": "customers report demand and pricing is visible"},
            {"result": "users need a simple workflow"},
        ],
    }


def test_build_spec_requires_build_decision():
    assert build_minimal_spec(None, _plan(), []) is None


def test_build_spec_is_conservative_and_explicit():
    spec = build_minimal_spec(_decision(), _plan(), [{"difficulty": "technical"}])
    assert spec is not None
    assert spec.title == "Simple SaaS"
    assert spec.mvp_scope == ("one workflow", "one metric")
    assert spec.cost_ceiling == "Rs 0 owner funding"
    assert "No owner capital." in spec.known_constraints
    assert spec.unknowns
