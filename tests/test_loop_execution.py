from core.brain import BrainDecision
from core.identity import NovaIdentity
from core.loop import run_continuous
from core.runtime import RuntimeState
from database.memory_repository import load_working_memory, save_working_memory
from memory.working import WorkingMemory
from database.schema import initialize_database


class SequencingBrain:
    def __init__(self):
        self.tasks = []
        self.previous_results = []

    def think(self, context):
        self.tasks.append(context.working_memory.get("current_task"))
        self.previous_results.append(context.working_memory.get("last_action_result"))

        if context.working_memory.get("last_action") == "record_observation":
            action = "system_status"
            plan = ["Record an observation", "Inspect system status"]
            task = "Inspect system status"
        else:
            action = "record_observation"
            plan = ["Record an observation", "Inspect system status"]
            task = "Record an observation"

        return BrainDecision(
            thought="Continue the current plan.",
            goal="Test sequential plan execution",
            plan=plan,
            action=action,
            reason="Advance to the next unresolved step.",
            action_input={},
        )


def test_result_interpreter_transitions_web_search_to_http_get():
    from core.result_interpreter import interpret_action_result

    result = """[BEGIN UNTRUSTED WEB SEARCH RESULTS]
Query: software opportunities
1. Candidate
   URL: https://example.com/opportunity
[END UNTRUSTED WEB SEARCH RESULTS]"""
    interpretation = interpret_action_result("web_search", result)

    assert interpretation.suggested_action == "http_get"
    assert interpretation.suggested_input == {"url": "https://example.com/opportunity"}


class RepeatingSearchBrain:
    def think(self, context):
        return BrainDecision(
            thought="Search again.",
            goal="Test continuation steering",
            plan=["Search", "Inspect the source"],
            action="web_search",
            reason="Search for information.",
            action_input={"query": "test"},
        )


def test_loop_steers_repeated_search_to_first_result(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "database.connection.DATABASE_PATH",
        tmp_path / "test.db",
    )
    initialize_database()

    memory = WorkingMemory(
        current_goal="Test continuation steering",
        current_task="Inspect the source",
        last_action="web_search",
        last_action_result=(
            "[BEGIN UNTRUSTED WEB SEARCH RESULTS]\n"
            "1. Candidate\n"
            "   URL: https://example.com\n"
            "[END UNTRUSTED WEB SEARCH RESULTS]"
        ),
    )
    save_working_memory(memory)
    loaded = load_working_memory()
    assert loaded.last_action == "web_search"
    assert loaded.last_action_result.startswith("[BEGIN UNTRUSTED WEB SEARCH RESULTS]")
    from core.result_interpreter import interpret_action_result
    assert interpret_action_result(
        loaded.last_action,
        loaded.last_action_result,
    ).suggested_action == "http_get"

    runtime = RuntimeState(brain=RepeatingSearchBrain())
    runtime.start()

    results = run_continuous(
        runtime,
        NovaIdentity(),
        interval_seconds=0,
        max_cycles=1,
    )

    assert results[0]["decision"] == "web_search"
    assert results[0]["action"].startswith((
        "[BEGIN UNTRUSTED WEB SEARCH RESULTS]",
        "No search results found",
        "Search failed:",
    ))


def test_loop_feeds_previous_result_into_next_cycle(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "database.connection.DATABASE_PATH",
        tmp_path / "test.db",
    )
    initialize_database()

    brain = SequencingBrain()
    runtime = RuntimeState(brain=brain)
    runtime.start()

    results = run_continuous(
        runtime,
        NovaIdentity(),
        interval_seconds=0,
        max_cycles=2,
    )

    assert len(results) == 2
    assert brain.previous_results[0] in (None, "")
    assert "Observation recorded successfully." in brain.previous_results[1]
    assert load_working_memory().last_action == "system_status"
    assert results[1]["decision"] == "system_status"
