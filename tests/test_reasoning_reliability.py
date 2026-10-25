from core.brain import BrainContext, NovaBrain
from core.providers.base import ModelResponse


def context() -> BrainContext:
    return BrainContext(
        identity={"name": "NOVA", "balance": 0.0},
        working_memory={
            "current_goal": "Become financially self-sustaining",
            "current_task": "Find a legitimate opportunity",
        },
        observation="Runtime online.",
        available_actions=["web_search", "record_observation"],
        tool_descriptions={
            "web_search": "Search the public web.",
            "record_observation": "Record the current observation.",
        },
    )


class RepairingProvider:
    def __init__(self):
        self.calls = 0

    def generate(self, prompt, system_prompt=""):
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(
                content='{"thought":123}',
                model="test",
                provider="test",
            )
        return ModelResponse(
            content='{"thought":"Repaired","goal":"Become financially self-sustaining","plan":["Search"],"action":"web_search","reason":"Need evidence","action_input":{"query":"legitimate software opportunities"}}',
            model="test",
            provider="test",
        )


class AlwaysInvalidProvider:
    def generate(self, prompt, system_prompt=""):
        return ModelResponse(
            content='not json',
            model="test",
            provider="test",
        )


def test_brain_repairs_invalid_model_response():
    provider = RepairingProvider()
    decision = NovaBrain(provider=provider).think(context())

    assert provider.calls == 2
    assert decision.thought == "Repaired"
    assert decision.action == "web_search"
    assert decision.action_input["query"] == "legitimate software opportunities"


def test_brain_falls_back_after_failed_repair():
    decision = NovaBrain(provider=AlwaysInvalidProvider()).think(context())

    assert decision.action == "record_observation"
    assert "repair failed" in decision.reason.lower()
