import json

from core.providers.base import LLMProvider, ModelResponse


class MockProvider(LLMProvider):
    def __init__(self, model: str = "mock-model") -> None:
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> ModelResponse:
        response = json.dumps(
            {
                "thought": "I should inspect the current state.",
                "goal": "Become financially self-sustaining",
                "plan": [
                    "Review the current state.",
                    "Evaluate available actions.",
                    "Record the observation.",
                ],
                "action": "record_observation",
                "reason": "This is the currently permitted action.",
                "action_input": {
                    "query": "financial",
                },
            }
        )
        return ModelResponse(
            content=response,
            model=self.model,
            provider="mock",
        )
