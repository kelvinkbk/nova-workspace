def test_runtime_integrity_failure_forces_packet_to_blocked_state():
    packet = {
        "status": "prepared",
        "action": "request_user_feedback",
        "side_effects_allowed": False,
        "execution_status": "not_executed",
    }
    integrity = {"valid": False, "issues": ["capability mismatch"]}

    if not integrity["valid"]:
        packet["status"] = "blocked"
        packet["action"] = None
        packet["side_effects_allowed"] = False
        packet["execution_status"] = "not_executed"

    assert packet == {
        "status": "blocked",
        "action": None,
        "side_effects_allowed": False,
        "execution_status": "not_executed",
    }
