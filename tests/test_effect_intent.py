from datetime import datetime, timezone, timedelta
import hashlib

from core.effect_intent import build_effect_intent, validate_effect_intent


def _intent(**overrides):
    now = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    payload = hashlib.sha256(b"hello").hexdigest()
    values = {
        "kind": "publish_static_site",
        "target": "static-site:staging",
        "payload_hash": payload,
        "purpose": "Publish a harmless validation artifact.",
        "cost_limit": 0,
        "reversibility": "reversible",
        "expires_at": now + timedelta(minutes=30),
        "capability_request_fingerprint": "capability-fingerprint",
        "requested_at": now,
    }
    values.update(overrides)
    return build_effect_intent(**values)


def test_valid_effect_intent_passes():
    result = validate_effect_intent(
        _intent(),
        now=datetime(2026, 10, 8, 12, 5, tzinfo=timezone.utc),
    )
    assert result["valid"] is True
    assert result["issues"] == []


def test_unknown_effect_kind_is_rejected():
    result = validate_effect_intent(
        _intent(kind="arbitrary_network_action"),
        now=datetime(2026, 10, 8, 12, 5, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Unknown effect kind is rejected." in result["issues"]


def test_tampered_intent_fingerprint_is_rejected():
    intent = _intent()
    tampered = type(intent)(**{**intent.to_dict(), "target": "different-target"})
    result = validate_effect_intent(
        tampered,
        now=datetime(2026, 10, 8, 12, 5, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Effect intent fingerprint does not match its contents." in result["issues"]


def test_expired_effect_intent_is_rejected():
    result = validate_effect_intent(
        _intent(),
        now=datetime(2026, 10, 8, 13, 0, tzinfo=timezone.utc),
    )
    assert result["valid"] is False
    assert "Effect intent has expired." in result["issues"]
