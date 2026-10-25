from core.validation_executor import advance_validation_plan, choose_validation_action


def _plan():
    return {
        "title": "Simple SaaS",
        "steps": ["a", "b", "c", "d", "e"],
        "cost_ceiling": "₹0 owner funding",
    }


def test_validation_executor_selects_permitted_actions():
    plan = _plan()
    first = choose_validation_action(plan)
    assert first.status == "ready"
    assert first.action == "memory_search"

    next_plan = advance_validation_plan(plan, first.action, "No stored demand evidence.")
    second = choose_validation_action(next_plan)
    assert next_plan["step_index"] == 1
    assert second.action == "web_search"


def test_validation_executor_blocks_before_real_world_side_effect():
    plan = _plan()
    for _ in range(4):
        action = choose_validation_action(plan)
        plan = advance_validation_plan(plan, action.action, "Useful evidence found.")

    action = choose_validation_action(plan)
    assert action.status == "blocked"
    assert action.action == "record_observation"
    assert plan["status"] == "blocked"


def test_validation_executor_does_not_advance_on_failed_action():
    plan = _plan()
    action = choose_validation_action(plan)
    plan = advance_validation_plan(plan, action.action, "Search failed: timeout")
    assert plan["step_index"] == 0
    assert plan["status"] == "ready"
