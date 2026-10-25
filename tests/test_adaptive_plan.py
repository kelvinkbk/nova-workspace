from core.brain import BrainDecision
from core.runtime import RuntimeState
from memory.working import WorkingMemory


def test_adaptive_plan_is_initialized_from_decision():
    runtime = RuntimeState()
    decision = BrainDecision(
        thought="Create a plan.",
        goal="Become financially self-sustaining",
        plan=[
            "Search for legitimate opportunities",
            "Review the best candidates",
        ],
        action="record_observation",
        reason="Test planning.",
    )
    policy = runtime.policy.evaluate(decision.action)

    memory = runtime.update_adaptive_plan(
        {"current_goal": decision.goal},
        decision,
        policy,
        "Observation recorded successfully.",
    )

    assert memory.plan_steps == [
        "Search for legitimate opportunities",
        "Review the best candidates",
    ]
    assert memory.plan_index == 1
    assert memory.current_task == "Review the best candidates"


def test_adaptive_plan_does_not_advance_failed_action():
    runtime = RuntimeState()
    memory = WorkingMemory()
    memory.set_goal("Become financially self-sustaining")
    memory.set_plan(
        [
            "Search for opportunities",
            "Review results",
        ],
        memory.current_goal,
    )

    decision = BrainDecision(
        thought="Search failed.",
        goal="Become financially self-sustaining",
        plan=memory.plan_steps,
        action="web_search",
        reason="Search the public web.",
    )
    policy = runtime.policy.evaluate(decision.action)

    updated = runtime.update_adaptive_plan(
        memory.to_dict(),
        decision,
        policy,
        "Search failed: timeout",
    )

    assert updated.plan_index == 0
    assert updated.current_task == "Search for opportunities"


def test_adaptive_plan_resets_when_goal_changes():
    runtime = RuntimeState()
    memory = WorkingMemory()
    memory.set_goal("Old goal")
    memory.set_plan(["Old step"], "Old goal")

    decision = BrainDecision(
        thought="New goal.",
        goal="New goal",
        plan=["New step 1", "New step 2"],
        action="record_observation",
        reason="New plan.",
    )
    policy = runtime.policy.evaluate(decision.action)

    updated = runtime.update_adaptive_plan(
        memory.to_dict(),
        decision,
        policy,
        "Observation recorded successfully.",
    )

    assert updated.plan_goal == "New goal"
    assert updated.plan_steps == ["New step 1", "New step 2"]
    assert updated.plan_index == 1
    assert updated.current_task == "New step 2"
