from security.policy import SecurityPolicy


def test_allowed_action():
    policy = SecurityPolicy()
    decision = policy.evaluate("record_observation")
    assert decision.allowed is True
    assert decision.action == "record_observation"


def test_unknown_action_is_denied():
    policy = SecurityPolicy()
    decision = policy.evaluate("transfer_money")
    assert decision.allowed is False
    assert decision.action == "transfer_money"
    assert decision.reason


def test_policy_actions_are_not_mutable():
    policy = SecurityPolicy()
    assert "record_observation" in policy._ALLOWED_ACTIONS
    try:
        policy._ALLOWED_ACTIONS.add("transfer_money")
        mutated = True
    except AttributeError:
        mutated = False
    assert mutated is False
    assert "transfer_money" not in policy._ALLOWED_ACTIONS
