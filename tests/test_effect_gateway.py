from datetime import datetime, timezone, timedelta
import hashlib

from core.effect_gateway import EffectGateway
from core.effect_grant import build_scoped_effect_grant
from core.effect_intent import build_effect_intent


def _intent():
    now = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
    return build_effect_intent(
        kind="publish_static_site",
        target="static-site:staging",
        payload_hash=hashlib.sha256(b"hello").hexdigest(),
        purpose="Dry-run publish.",
        cost_limit=0,
        reversibility="reversible",
        expires_at=now + timedelta(minutes=30),
        capability_request_fingerprint="capability-fingerprint",
        requested_at=now,
    )


def _grant(intent):
    now = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
    return build_scoped_effect_grant(
        intent,
        max_cost=0,
        expires_at=now + timedelta(minutes=20),
        capability_request_fingerprint=intent.capability_request_fingerprint,
    )


def test_gateway_dry_run_has_zero_side_effects():
    gateway = EffectGateway()
    intent = _intent()
    result = gateway.submit(
        intent,
        grant=_grant(intent),
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
    )

    assert result["status"] == "dry_run"
    assert result["executed"] is False
    assert result["side_effects"] is False
    assert len(gateway.outbox()) == 1


def test_gateway_rejects_invalid_intent_before_outbox():
    gateway = EffectGateway()
    intent = _intent()
    tampered = type(intent)(**{**intent.to_dict(), "target": ""})

    result = gateway.submit(
        tampered,
        grant=_grant(intent),
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
    )

    assert result["status"] == "rejected"
    assert result["executed"] is False
    assert result["side_effects"] is False
    assert gateway.outbox() == []


def test_gateway_rejects_missing_grant():
    gateway = EffectGateway()
    result = gateway.submit(
        _intent(),
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
    )

    assert result["status"] == "rejected"
    assert result["executed"] is False
    assert result["side_effects"] is False
    assert gateway.outbox() == []


def test_gateway_rejects_expired_grant():
    gateway = EffectGateway()
    intent = _intent()
    result = gateway.submit(
        intent,
        grant=_grant(intent),
        now=datetime(2026, 10, 9, 13, 0, tzinfo=timezone.utc),
    )

    assert result["status"] == "rejected"
    assert result["executed"] is False
    assert result["side_effects"] is False
    assert gateway.outbox() == []


def test_gateway_cannot_live_execute_in_m102():
    gateway = EffectGateway()
    intent = _intent()
    result = gateway.submit(
        intent,
        grant=_grant(intent),
        now=datetime(2026, 10, 9, 12, 5, tzinfo=timezone.utc),
        dry_run=False,
    )

    assert result["status"] == "blocked"
    assert result["executed"] is False
    assert result["side_effects"] is False
    assert gateway.outbox() == []
