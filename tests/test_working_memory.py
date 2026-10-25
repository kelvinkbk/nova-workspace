from memory.working import WorkingMemory

def test_working_memory():
    memory = WorkingMemory()
    memory.set_goal("Become financially self-sustaining")
    memory.set_task("Find the first legitimate earning opportunity")
    memory.set_project("NOVA")
    memory.add_note("Starting balance is ₹0")
    state = memory.to_dict()
    assert state["current_goal"] == "Become financially self-sustaining"
    assert state["current_task"] == "Find the first legitimate earning opportunity"
    assert state["active_project"] == "NOVA"
    assert "Starting balance is ₹0" in state["notes"]

    memory.set_plan(
        [
            "Search for opportunities",
            "Review results",
        ],
        memory.current_goal,
    )
    memory.advance_plan()
    state = memory.to_dict()
    assert state["plan_steps"] == [
        "Search for opportunities",
        "Review results",
    ]
    assert state["plan_index"] == 1
    assert state["current_task"] == "Review results"

    memory.last_action = "web_search"
    memory.last_action_result = "Found five candidate opportunities."
    memory.last_reflection = "Use the result as evidence."
    state = memory.to_dict()
    assert state["last_action"] == "web_search"
    assert state["last_action_result"] == "Found five candidate opportunities."
    assert state["last_reflection"] == "Use the result as evidence."