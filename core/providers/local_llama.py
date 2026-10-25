import json
from urllib.request import Request, urlopen

from core.providers.base import LLMProvider, ModelResponse


class LocalLlamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080/v1",
        model: str = "/E/local ai/models/Qwen2.5-Coder-1.5B-Q4_K_M.gguf",
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> ModelResponse:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": 256,
            "response_format": {
                "type": "json_object",
            },
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return ModelResponse(
            content=content,
            model=self.model,
            provider="llama.cpp",
        )
