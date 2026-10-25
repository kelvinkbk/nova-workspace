from datetime import datetime, timezone, timedelta

from core.capability_approval import record_capability_approval
from core.capability_approval_integrity import verify_capability_approval


def _request():
    return {
        "status": "approval_required",
        "requested": ["real_world_user_interaction"],
        "unavailable": ["real_world_user_interaction"],
        "approval_required": True,
    }


def test_matching_fresh_approval_passes():
    issued = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
        ttl_seconds=3600,
    ).to_dict()

    result = verify_capability_approval(
        _request(),
        approval,
        now=issued + timedelta(minutes=30),
    )

    assert result.valid is True


def test_expired_approval_fails():
    issued = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
        ttl_seconds=3600,
    ).to_dict()

    result = verify_capability_approval(
        _request(),
        approval,
        now=issued + timedelta(hours=1),
    )

    assert result.valid is False
    assert "expired" in result.reason


def test_future_approval_fails():
    issued = datetime(2026, 10, 8, 13, 0, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
        ttl_seconds=3600,
    ).to_dict()

    result = verify_capability_approval(
        _request(),
        approval,
        now=issued - timedelta(seconds=1),
    )

    assert result.valid is False


def test_changed_request_still_invalidates_approval():
    issued = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
    ).to_dict()
    changed = dict(_request())
    changed["requested"] = ["browser"]

    result = verify_capability_approval(
        changed,
        approval,
        now=issued + timedelta(minutes=1),
    )

    assert result.valid is False


def test_tampered_activation_flag_fails_closed():
    issued = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
    ).to_dict()
    approval["activation_allowed"] = True

    result = verify_capability_approval(
        _request(),
        approval,
        now=issued + timedelta(minutes=1),
    )

    assert result.valid is False
