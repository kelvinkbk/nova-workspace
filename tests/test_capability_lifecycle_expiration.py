from datetime import datetime, timedelta, timezone

from core.capability_approval import record_capability_approval
from core.capability_lifecycle import validate_capability_lifecycle


def _request():
    return {
        "status": "approval_required",
        "requested": ["browser"],
        "unavailable": ["browser"],
        "approval_required": True,
    }


def test_lifecycle_marks_expired_approval_terminal():
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(), "approve", issued_at=issued, ttl_seconds=60
    ).to_dict()

    result = validate_capability_lifecycle(
        _request(), approval, now=issued + timedelta(seconds=60)
    )

    assert result.valid is True
    assert result.status == "expired"
    assert "fresh approval" in result.reason


def test_lifecycle_keeps_fresh_approval_pending():
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(), "approve", issued_at=issued, ttl_seconds=60
    ).to_dict()

    result = validate_capability_lifecycle(
        _request(), approval, now=issued + timedelta(seconds=59)
    )

    assert result.valid is True
    assert result.status == "approved_pending_activation"
