from datetime import datetime, timedelta, timezone

from core.capability_approval import record_capability_approval
from core.capability_approval_expiration import (
    approval_is_expired,
    expire_capability_approval,
)


def _request():
    return {
        "status": "approval_required",
        "requested": ["browser"],
        "unavailable": ["browser"],
        "approval_required": True,
    }


def test_expiration_detects_expired_approval():
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
        ttl_seconds=60,
    ).to_dict()

    assert approval_is_expired(
        approval,
        now=issued + timedelta(seconds=60),
    ) is True


def test_expiration_does_not_touch_fresh_approval():
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
        ttl_seconds=60,
    ).to_dict()

    assert approval_is_expired(
        approval,
        now=issued + timedelta(seconds=59),
    ) is False


def test_expire_materializes_terminal_state():
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
        ttl_seconds=60,
    ).to_dict()
    build_plan = {"capability_approval": approval}

    result = expire_capability_approval(
        build_plan,
        now=issued + timedelta(seconds=61),
    )

    assert result["status"] == "expired"
    assert result["activation_allowed"] is False
    assert build_plan["capability_approval"]["status"] == "expired"
    assert build_plan["capability_approval_history"][-1]["status"] == "expired"
    assert build_plan["capability_approval_history"][-1]["decision"] == "expire"


def test_fresh_approval_cannot_be_expired():
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    approval = record_capability_approval(
        _request(),
        "approve",
        issued_at=issued,
        ttl_seconds=60,
    ).to_dict()
    build_plan = {"capability_approval": approval}

    result = expire_capability_approval(
        build_plan,
        now=issued + timedelta(seconds=30),
    )

    assert result["status"] == "rejected"
    assert build_plan["capability_approval"]["status"] == "approved_pending_activation"
