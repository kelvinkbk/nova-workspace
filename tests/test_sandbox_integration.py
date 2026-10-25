from core.brain import BrainDecision
from core.runtime import RuntimeState
from security.policy import SecurityPolicy
from tools.executor import ToolExecutor
from tools.registry import ToolDefinition, ToolRegistry
from tools.sandbox import sandbox_write_file


def test_sandbox_write_is_an_explicit_runtime_capability(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.sandbox.SANDBOX_ROOT", tmp_path / "sandbox")

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "sandbox_write",
            "Write only inside the isolated sandbox.",
            sandbox_write_file,
        )
    )
    executor = ToolExecutor(registry, SecurityPolicy())

    decision = BrainDecision(
        "build safely",
        "validated build",
        ["write prototype"],
        "sandbox_write",
        "Prototype only inside isolated sandbox.",
        {"path": "app/main.py", "content": "print('NOVA prototype')"},
    )

    assert SecurityPolicy().evaluate(decision.action).allowed is True
    result = executor.execute(decision.action, decision.action_input)

    assert result.startswith("Sandbox file written:")
    assert (tmp_path / "sandbox" / "app" / "main.py").exists()


def test_runtime_registers_sandbox_writer():
    runtime = RuntimeState()
    assert "sandbox_write" in runtime.registry.available_tools()
    assert runtime.authorize(
        BrainDecision("x", "y", [], "sandbox_write", "safe", {})
    ).allowed is True
