from core.brain import BrainDecision
from core.runtime import RuntimeState


def test_runtime_audits_missing_validation_approval_binding(monkeypatch):
    runtime = RuntimeState()

    monkeypatch.setattr(
        "core.runtime.record_experiment_result",
        lambda plan, action, result: dict(plan),
    )
    monkeypatch.setattr(
        "core.runtime.evaluate_experiment_result",
        lambda result: type(
            "Evaluation", (), {
                "status": "inconclusive",
                "to_dict": lambda self: {"status": self.status},
            }
        )(),
    )
    monkeypatch.setattr(
        "core.runtime.create_followup_experiment",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "core.runtime.create_real_world_validation_gate",
        lambda *args, **kwargs: type(
            "Gate", (), {
                "to_dict": lambda self: {},
                "next_action": "record_observation",
            }
        )(),
    )
    monkeypatch.setattr(
        "core.runtime.create_validation_request_spec",
        lambda *args, **kwargs: type(
            "Spec", (), {
                "required_capabilities": ["real_world_user_interaction"],
                "to_dict": lambda self: {
                    "required_capabilities": self.required_capabilities
                },
            }
        )(),
    )
    monkeypatch.setattr(
        "core.runtime.build_real_world_validation_request",
        lambda spec: type(
            "Packet", (), {
                "to_dict": lambda self: {
                    "status": "prepared",
                    "required_capabilities": ["real_world_user_interaction"],
                }
            }
        )(),
    )
    monkeypatch.setattr(
        "core.runtime.validate_real_world_validation_request_integrity",
        lambda packet, request: {"valid": True, "issues": []},
    )
    monkeypatch.setattr(
        "core.runtime.validate_real_world_validation_approval_enforcement",
        lambda binding, enforcement, packet: {
            "valid": False,
            "issues": ["forced consistency failure"],
        },
    )
    monkeypatch.setattr(
        "core.runtime.create_capability_request",
        lambda *args, **kwargs: type(
            "Request", (), {
                "to_dict": lambda self: {
                    "requested": ["real_world_user_interaction"]
                }
            }
        )(),
    )

    state = {
        "current_goal": "test",
        "build_plan": {
            "status": "sandbox_complete",
            "followup_experiment": {
                "status": "ready",
                "title": "Follow up",
                "purpose": "test",
            },
        },
    }
    memory = runtime.update_adaptive_plan(
        state,
        BrainDecision("test", "test", [], "web_search", "test", {"query": "test"}),
        type("Policy", (), {"allowed": True})(),
        "search result",
        available_actions=["web_search", "record_observation"],
    )

    binding = memory.build_plan["real_world_validation_approval_binding"]
    assert binding["valid"] is False
    assert "No capability approval is present." in binding["issues"]
    history = memory.build_plan["real_world_validation_approval_binding_history"]
    assert history[-1]["valid"] is False
    assert history[-1]["enforcement_status"] == "blocked"
    assert history[-1]["enforcement_reason"] == "Validation approval enforcement consistency failed; execution remains disabled."
    packet = memory.build_plan["real_world_validation_request_packet"]
    assert packet["status"] == "blocked"
    assert packet["action"] is None
    assert packet["side_effects_allowed"] is False
    assert packet["execution_status"] == "not_executed"
    enforcement = memory.build_plan["real_world_validation_approval_binding_enforcement"]
    assert enforcement["status"] == "blocked"
    assert enforcement["reason"] == "Validation approval enforcement consistency failed; execution remains disabled."
    assert enforcement["issues"] == ["forced consistency failure"]
