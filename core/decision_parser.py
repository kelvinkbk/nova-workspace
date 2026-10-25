from __future__ import annotations

import json


def parse_brain_decision(content: str, fallback_goal: str) -> BrainDecision:
    from core.brain import BrainDecision

    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise ValueError("LLM response must be a JSON object.")
    required_fields = {
        "thought",
        "goal",
        "plan",
        "action",
        "reason",
    }
    missing = required_fields - data.keys()
    if missing:
        raise ValueError(
            f"LLM response is missing fields: {sorted(missing)}"
        )
    if not isinstance(data["thought"], str):
        raise ValueError("thought must be a string.")
    if not isinstance(data["goal"], str):
        raise ValueError("goal must be a string.")
    if not isinstance(data["plan"], list):
        raise ValueError("plan must be a list.")
    if not all(isinstance(step, str) for step in data["plan"]):
        raise ValueError("Every plan step must be a string.")
    if not isinstance(data["action"], str):
        raise ValueError("action must be a string.")
    if not isinstance(data["reason"], str):
        raise ValueError("reason must be a string.")
    action_input = data.get("action_input", {})
    if not isinstance(action_input, dict):
        raise ValueError("action_input must be an object.")
    goal = data["goal"].strip() or fallback_goal
    action = data["action"].strip()
    if not action:
        raise ValueError("action cannot be empty.")
    return BrainDecision(
        thought=data["thought"],
        goal=goal,
        plan=data["plan"],
        action=action,
        reason=data["reason"],
        action_input=action_input,
    )
