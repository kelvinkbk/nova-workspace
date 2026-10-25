from core.brain import BrainDecision
from core.runtime import RuntimeState


def test_reflection_evaluates_completed_result():
    runtime = RuntimeState()
    decision = BrainDecision(
        thought="Inspect the system.",
        goal="Test reflection",
        plan=["Inspect system state."],
        action="system_status",
        reason="System status should provide machine state.",
    )
    policy_decision = runtime.policy.evaluate(decision.action)

    reflection = runtime.reflect(
        decision,
        "OS: Windows 11",
        policy_decision,
    )

    assert "decision=system_status" in reflection
    assert "expected=System status should provide machine state." in reflection
    assert "actual=OS: Windows 11" in reflection
    assert "outcome=completed" in reflection
    assert "next_step=Use this result as evidence for the next decision." in reflection


def test_reflection_detects_blocked_result():
    runtime = RuntimeState()
    decision = BrainDecision(
        thought="Request blocked action.",
        goal="Test reflection",
        plan=["Attempt blocked action."],
        action="transfer_money",
        reason="Test policy boundary.",
    )
    policy_decision = runtime.policy.evaluate(decision.action)

    reflection = runtime.reflect(
        decision,
        "Action denied: transfer_money.",
        policy_decision,
    )

    assert "outcome=blocked" in reflection
    assert "Choose an action permitted by the security policy." in reflection
