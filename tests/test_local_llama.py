import json

from core.providers.local_llama import LocalLlamaProvider


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def read(self):
        return json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "LOCAL MODEL RESPONSE",
                        }
                    }
                ]
            }
        ).encode("utf-8")


def test_local_llama_provider(monkeypatch):
    def fake_urlopen(request, timeout):
        assert request.full_url == (
            "http://127.0.0.1:8080/v1/chat/completions"
        )
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == (
            "/E/local ai/models/Qwen2.5-Coder-1.5B-Q4_K_M.gguf"
        )
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][1]["role"] == "user"
        assert body["messages"][1]["content"] == "Hello NOVA"
        assert timeout == 120
        return FakeResponse()

    monkeypatch.setattr("core.providers.local_llama.urlopen", fake_urlopen)
    provider = LocalLlamaProvider()
    response = provider.generate(
        prompt="Hello NOVA",
        system_prompt="You are NOVA.",
    )
    assert response.content == "LOCAL MODEL RESPONSE"
    assert response.provider == "llama.cpp"
    assert response.model == "/E/local ai/models/Qwen2.5-Coder-1.5B-Q4_K_M.gguf"
