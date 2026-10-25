import json

from core.providers.base import ModelResponse
from core.providers.mock import MockProvider


def test_mock_provider_implements_llm_interface():
    provider = MockProvider()
    response = provider.generate(
        prompt="What is NOVA?",
        system_prompt="You are NOVA.",
    )
    assert isinstance(response, ModelResponse)
    assert response.provider == "mock"
    assert response.model == "mock-model"
    data = json.loads(response.content)
    assert data["action"] == "record_observation"
    assert data["thought"]


def test_provider_can_use_custom_model_name():
    provider = MockProvider(model="test-model")
    response = provider.generate("Hello")
    assert response.model == "test-model"
