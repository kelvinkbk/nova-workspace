from core.brain import BrainDecision
from core.runtime import RuntimeState
from database.memory_repository import load_episodes, load_journal_entries
from database.schema import initialize_database


def test_runtime_lifecycle():
    initialize_database()
    runtime = RuntimeState()
    assert runtime.status == "OFFLINE"
    assert runtime.cycle == 0
    runtime.start()
    assert runtime.status == "ONLINE"
    assert runtime.started_at is not None
    result = runtime.run_cycle(
        life_day=1,
        identity={
            "name": "NOVA",
            "balance": 0.0,
        },
        working_memory={
            "current_goal": "Become financially self-sustaining",
        },
        available_actions=[
            "record_observation",
        ],
    )
    assert runtime.cycle == 1
    assert result["cycle"] == 1
    assert result["goal"] == "Become financially self-sustaining"
    assert result["decision"] == "record_observation"
    assert result["policy_allowed"] is True
    assert runtime.last_action == "record_observation"
    episodes = load_episodes()
    journals = load_journal_entries()
    assert episodes[0].event == "NOVA cognitive cycle executed"
    assert journals[0].title == "Cognitive cycle 1"
    runtime.stop()


def test_runtime_denies_transfer_money():
    initialize_database()

    class DangerousBrain:
        def think(self, context):
            return BrainDecision(
                thought="Requesting a dangerous action.",
                goal="Protect funds",
                plan=["Request transfer"],
                action="transfer_money",
                reason="Test policy boundary.",
            )

    runtime = RuntimeState(brain=DangerousBrain())
    runtime.start()
    result = runtime.run_cycle(
        life_day=1,
        working_memory={"current_goal": "Protect funds"},
        available_actions=["transfer_money"],
    )
    assert result["decision"] == "transfer_money"
    assert result["policy_allowed"] is False
    assert result["action"].startswith("Action denied: transfer_money.")
    assert runtime.last_action is None


def test_runtime_builds_workspace_context():
    runtime = RuntimeState()
    context = runtime.build_workspace_context()

    assert "Workspace root:" in context
    assert "core/identity.py" in context
    assert "security/policy.py" in context


def test_runtime_passes_tool_purposes_to_brain():
    class InspectingBrain:
        def __init__(self):
            self.context = None

        def think(self, context):
            self.context = context
            return BrainDecision(
                thought="Inspecting available capabilities.",
                goal="Learn about the world.",
                plan=["Use the appropriate read-only tool."],
                action="record_observation",
                reason="Test decision.",
            )

    brain = InspectingBrain()
    runtime = RuntimeState(brain=brain)
    runtime.start()

    runtime.think(
        observation="Runtime is online.",
        working_memory={"current_goal": "Learn about the world."},
        available_actions=["web_search", "system_status"],
    )

    assert brain.context.tool_descriptions["web_search"].startswith("Search the public web")
    assert brain.context.tool_descriptions["system_status"].startswith("Read basic system information")


def test_runtime_recall_memory_uses_current_goal():
    runtime = RuntimeState()
    recalled = runtime.recall_memory(
        {"current_goal": "Become financially self-sustaining"}
    )

    assert isinstance(recalled, list)
    assert len(recalled) <= 5


def test_runtime_recall_memory_returns_empty_without_goal_or_task():
    runtime = RuntimeState()

    assert runtime.recall_memory({}) == []


def test_runtime_requires_online_status():
    runtime = RuntimeState()
    try:
        runtime.run_cycle()
        raised = False
    except RuntimeError:
        raised = True
    assert raised is True


def test_runtime_executes_allowed_tool():
    initialize_database()
    runtime = RuntimeState()
    runtime.start()
    result = runtime.run_cycle(
        life_day=1,
        identity={
            "name": "NOVA",
            "balance": 0.0,
        },
        working_memory={
            "current_goal": "Become financially self-sustaining",
        },
        available_actions=[
            "record_observation",
        ],
    )
    assert result["policy_allowed"] is True
    assert result["decision"] == "record_observation"
    assert result["action"] == "Observation recorded successfully."
