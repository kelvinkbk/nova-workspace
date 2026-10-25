from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelResponse:
    content: str
    model: str
    provider: str


class LLMProvider(ABC):
    """
    Common interface for all NOVA language-model providers.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> ModelResponse:
        raise NotImplementedError
