import json

import pytest

from core.decision_parser import parse_brain_decision


def valid_decision() -> str:
    return json.dumps(
        {
            "thought": "I should inspect the current state.",
            "goal": "Become financially self-sustaining",
            "plan": [
                "Review current state",
                "Evaluate permitted actions",
            ],
            "action": "record_observation",
            "reason": "This action is currently permitted.",
        }
    )


def test_parse_valid_decision():
    decision = parse_brain_decision(
        valid_decision(),
        fallback_goal="Fallback goal",
    )
    assert decision.thought == "I should inspect the current state."
    assert decision.goal == "Become financially self-sustaining"
    assert decision.plan == [
        "Review current state",
        "Evaluate permitted actions",
    ]


def test_parse_markdown_fenced_decision():
    decision = parse_brain_decision(
        f"```json\n{valid_decision()}\n```",
        fallback_goal="Fallback goal",
    )
    assert decision.action == "record_observation"


def test_parse_missing_field():
    data = json.loads(valid_decision())
    del data["reason"]
    with pytest.raises(ValueError, match="missing fields"):
        parse_brain_decision(json.dumps(data), fallback_goal="Fallback goal")


def test_parse_invalid_plan_step():
    data = json.loads(valid_decision())
    data["plan"] = ["Review current state", 1]
    with pytest.raises(ValueError, match="Every plan step"):
        parse_brain_decision(json.dumps(data), fallback_goal="Fallback goal")


def test_parse_empty_goal_and_action():
    data = json.loads(valid_decision())
    data["goal"] = "   "
    data["action"] = "record_observation"
    decision = parse_brain_decision(
        json.dumps(data),
        fallback_goal="Fallback goal",
    )
    assert decision.goal == "Fallback goal"

    data["action"] = "   "
    with pytest.raises(ValueError, match="action cannot be empty"):
        parse_brain_decision(json.dumps(data), fallback_goal="Fallback goal")


def test_parse_action_input():
    data = json.loads(valid_decision())
    data["action_input"] = {"query": "financial"}
    decision = parse_brain_decision(
        json.dumps(data),
        fallback_goal="Fallback goal",
    )
    assert decision.action_input == {"query": "financial"}


def test_action_input_must_be_object():
    data = json.loads(valid_decision())
    data["action_input"] = "financial"
    with pytest.raises(ValueError, match="action_input must be an object"):
        parse_brain_decision(json.dumps(data), fallback_goal="Fallback goal")
