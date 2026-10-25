from core.brain import BrainDecision
from core.identity import NovaIdentity
from core.loop import run_continuous
from core.runtime import RuntimeState
from database.memory_repository import save_working_memory
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_progress_controller_changes_repeated_action():
    runtime = RuntimeState()
    chosen = runtime.choose_progress_action(
        "system_status",
        ["system_status", "web_search", "record_observation"],
        "Become financially self-sustaining",
    )
    assert chosen == "web_search"


def test_progress_controller_returns_alternate_action_for_non_finance_goal():
    runtime = RuntimeState()
    chosen = runtime.choose_progress_action(
        "system_status",
        ["system_status", "environment_map"],
        "Understand the environment",
    )
    assert chosen == "environment_map"


def test_action_input_is_normalized_from_goal():
    runtime = RuntimeState()
    decision = BrainDecision(
        thought="Search.",
        goal="Find legitimate software income",
        plan=["Search"],
        action="web_search",
        reason="Search the web.",
        action_input={},
    )
    normalized = runtime.normalize_action_input(
        decision,
        {"current_goal": "Find legitimate software income"},
    )
    assert normalized.action_input["query"] == "Find legitimate software income"


class RepeatingStatusBrain:
    def think(self, context):
        return BrainDecision(
            thought="Check system again.",
            goal="Become financially self-sustaining",
            plan=["Inspect state", "Find earning opportunities"],
            action="system_status",
            reason="Inspect the current state.",
            action_input={},
        )


def test_runtime_detects_stagnation_and_changes_action(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "database.connection.DATABASE_PATH",
        tmp_path / "test.db",
    )
    initialize_database()

    memory = WorkingMemory(
        current_goal="Become financially self-sustaining",
        current_task="Find earning opportunities",
        last_action="system_status",
        last_action_result="OS: Windows 11",
    )
    save_working_memory(memory)

    runtime = RuntimeState(brain=RepeatingStatusBrain())
    runtime.start()

    result = runtime.run_cycle(
        life_day=1,
        identity=NovaIdentity().to_dict(),
        working_memory=memory.to_dict(),
        available_actions=["system_status", "web_search", "record_observation"],
    )

    assert result["decision"] == "web_search"
    assert result["stagnation_detected"] is True


class RepeatingSearchBrain:
    def think(self, context):
        return BrainDecision(
            thought="Search again.",
            goal="Become financially self-sustaining",
            plan=["Search", "Inspect the source"],
            action="web_search",
            reason="Search for information.",
            action_input={"query": "test"},
        )


def test_concrete_continuation_overrides_repeat(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "database.connection.DATABASE_PATH",
        tmp_path / "test.db",
    )
    initialize_database()

    memory = WorkingMemory(
        current_goal="Become financially self-sustaining",
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

    runtime = RuntimeState(brain=RepeatingSearchBrain())
    runtime.start()

    result = runtime.run_cycle(
        life_day=1,
        identity=NovaIdentity().to_dict(),
        working_memory=memory.to_dict(),
        available_actions=["web_search", "http_get", "record_observation"],
    )

    assert result["decision"] == "http_get"
