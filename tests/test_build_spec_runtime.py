from core.brain import BrainDecision
from core.opportunity_evaluator import OpportunitySelection, OpportunityValidation
from core.runtime import RuntimeState
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_runtime_builds_and_persists_minimal_spec(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    monkeypatch.setattr(
        "core.runtime.select_best_opportunity",
        lambda evidence, goal: OpportunitySelection(
            "selected", "Simple SaaS", "https://example.com/saas", 12,
            ("explicit monetization",), len(evidence)
        ),
    )
    monkeypatch.setattr(
        "core.runtime.check_selected_opportunity",
        lambda selected, evidence: OpportunityValidation(
            "validated", selected["title"], selected["url"],
            ("monetization is explicit", "startup signal is compatible with a zero-cost start", "evidence confidence is medium"),
            ("monetization", "zero-cost-compatible startup", "medium confidence"),
            len(evidence),
        ),
    )

    runtime = RuntimeState()
    memory = WorkingMemory(
        current_goal="software income",
        selected_opportunity={
            "status": "selected",
            "title": "Simple SaaS",
            "url": "https://example.com/saas",
            "validation": {"status": "validated"},
        },
        validation_plan={
            "title": "Simple SaaS",
            "status": "ready",
            "step_index": 4,
            "steps": ["a", "b", "c", "d", "e"],
            "observations": [
                {"step_index": 0, "result": "customers report demand and pricing"},
                {"step_index": 1, "result": "users need the problem solved"},
                {"step_index": 2, "result": "paying customers and revenue exist"},
                {"step_index": 3, "result": "free distribution is possible"},
            ],
        },
        opportunity_evidence=[
            {
                "url": "https://example.com/saas",
                "title": "Simple SaaS",
                "monetization": "subscription",
                "startup_cost": "explicitly mentions a free/no-upfront option",
                "capital_fit": "promising for zero start",
                "confidence": "medium",
            }
        ],
    )
    decision = BrainDecision(
        "Complete validation research",
        "software income",
        ["Complete validation research"],
        "record_observation",
        "Finish research-only validation.",
        {},
    )

    runtime.status = "ONLINE"
    updated = runtime.update_adaptive_plan(
        memory.to_dict(), decision, runtime.authorize(decision), "Observation recorded."
    )

    assert updated.build_decision["status"] == "build_minimal"
    assert updated.build_spec is not None
    assert updated.build_spec["title"] == "Simple SaaS"
    assert updated.current_task == "Review the smallest build plan before implementation."



def test_working_memory_round_trips_build_spec(tmp_path, monkeypatch):
    from database.memory_repository import load_working_memory, save_working_memory

    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "test.db")
    initialize_database()

    memory = WorkingMemory(
        current_goal="software income",
        build_decision={"status": "build_minimal", "title": "Simple SaaS"},
        build_spec={
            "title": "Simple SaaS",
            "problem_statement": "One problem",
            "target_user": "Narrow users",
            "mvp_scope": ["one workflow"],
            "distribution_path": "free channel",
            "success_metric": "one demand signal",
            "cost_ceiling": "Rs 0 owner funding",
            "known_constraints": ["No owner capital."],
            "unknowns": ["Exact segment"],
        },
    )
    save_working_memory(memory)

    loaded = load_working_memory()
    assert loaded.build_spec["title"] == "Simple SaaS"
    assert loaded.build_spec["mvp_scope"] == ["one workflow"]
