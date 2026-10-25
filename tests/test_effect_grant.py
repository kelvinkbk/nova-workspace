from datetime import datetime, timezone, timedelta
import hashlib

from core.effect_grant import build_scoped_effect_grant, validate_scoped_effect_grant
from core.effect_intent import build_effect_intent


def _intent(**overrides):
    now = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
    values = {
        "kind": "publish_static_site",
        "target": "static-site:staging",
        "payload_hash": hashlib.sha256(b"hello").hexdigest(),
        "purpose": "Scoped grant test.",
        "cost_limit": 5,
        "reversibility": "reversible",
        "expires_at": now + timedelta(minutes=30),
        "capability_request_fingerprint": "capability-fingerprint",
        "requested_at": now,
    }
    values.update(overrides)
    return build_effect_intent(**values)


def _grant(intent, **overrides):
    now = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
    values = {
        "max_cost": 5,
        "expires_at": now + timedelta(minutes=20),
        "capability_request_fingerprint": intent.capability_request_fingerprint,
    }
    values.update(overrides)
    return build_scoped_effect_grant(intent, **values)


def test_matching_scoped_grant_passes():
    intent = _intent()
    result = validate_scoped_effect_grant(
        intent,
        _grant(intent),
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
    )
    assert result["valid"] is True
    assert result["issues"] == []


def test_grant_rejects_intent_fingerprint_mismatch():
    intent = _intent()
    other = _intent(target="static-site:other")
    result = validate_scoped_effect_grant(
        intent,
        _grant(other),
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Scoped effect grant is not bound to this effect." in result["issues"]


def test_grant_rejects_target_mismatch():
    intent = _intent()
    grant = _grant(intent)
    tampered = type(grant)(**{**grant.to_dict(), "target": "different-target"})
    result = validate_scoped_effect_grant(
        intent,
        tampered,
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Scoped effect grant fingerprint does not match its contents." in result["issues"]


def test_grant_rejects_cost_over_limit():
    intent = _intent(cost_limit=10)
    result = validate_scoped_effect_grant(
        intent,
        _grant(intent, max_cost=5),
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Effect cost exceeds the scoped grant limit." in result["issues"]


def test_grant_rejects_expiry():
    intent = _intent()
    result = validate_scoped_effect_grant(
        intent,
        _grant(intent),
        now=datetime(2026, 10, 9, 13, 0, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Scoped effect grant has expired." in result["issues"]


def test_grant_cannot_activate_effect():
    intent = _intent()
    grant = _grant(intent, activation_allowed=True)
    result = validate_scoped_effect_grant(
        intent,
        grant,
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Scoped effect grant cannot activate effects directly." in result["issues"]
