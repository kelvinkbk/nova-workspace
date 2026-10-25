from datetime import datetime, timedelta, timezone
import hashlib

from core.effect_grant import build_scoped_effect_grant
from core.effect_grant_lifecycle import validate_effect_grant_lifecycle, transition_effect_grant_state
from core.effect_intent import build_effect_intent
from core.effect_grant_history import record_effect_grant_event


def _grant():
    now = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
    intent = build_effect_intent(
        kind="publish_static_site",
        target="static-site:staging",
        payload_hash=hashlib.sha256(b"x").hexdigest(),
        purpose="test",
        cost_limit=0,
        reversibility="reversible",
        expires_at=now + timedelta(minutes=30),
        capability_request_fingerprint="cap",
        requested_at=now,
    )
    return build_scoped_effect_grant(
        intent,
        max_cost=0,
        expires_at=now + timedelta(minutes=20),
        capability_request_fingerprint="cap",
    )


def test_active_grant_can_be_used():
    result = validate_effect_grant_lifecycle(
        _grant(), now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc)
    )
    assert result["valid"] is True
    assert result["status"] == "active"
    assert result["can_use"] is True


def test_expired_grant_becomes_terminal():
    result = validate_effect_grant_lifecycle(
        _grant(), now=datetime(2026, 10, 9, 13, 0, tzinfo=timezone.utc)
    )
    assert result == {"valid": True, "status": "expired", "issues": [], "can_use": False}


def test_terminal_state_cannot_transition():
    result = transition_effect_grant_state(
        _grant(), current_state="revoked", new_state="active"
    )
    assert result["valid"] is False


def test_active_grant_can_transition_to_revoked():
    result = transition_effect_grant_state(
        _grant(), current_state="active", new_state="revoked"
    )
    assert result["valid"] is True
    assert result["can_use"] is False


def test_history_is_bounded():
    grant = _grant()
    history = []
    lifecycle = {"valid": True, "status": "active", "can_use": True, "issues": []}
    for _ in range(25):
        history = record_effect_grant_event(history, grant, lifecycle, event="validated")
    assert len(history) == 20
    assert history[-1]["event"] == "validated"
