from core.capability_activation_preflight import preflight_capability_activation
from core.capability_approval import record_capability_approval
from core.capability_manifest import CapabilityManifest


def _request():
    return {
        "status": "approval_required",
        "requested": ["read_only_research"],
        "unavailable": [],
        "approval_required": True,
    }


def test_valid_approval_stays_blocked_when_activation_not_implemented():
    request = _request()
    approval = record_capability_approval(request, "approve").to_dict()

    result = preflight_capability_activation(
        request,
        approval,
        CapabilityManifest(),
    )

    assert result.status == "blocked"
    assert result.activation_allowed is False
    assert "not implemented" in result.reason


def test_tampered_approval_is_blocked():
    request = _request()
    approval = record_capability_approval(request, "approve").to_dict()
    approval["activation_allowed"] = True

    result = preflight_capability_activation(
        request,
        approval,
        CapabilityManifest(),
    )

    assert result.status == "blocked"
    assert result.activation_allowed is False


def test_missing_capability_is_blocked_even_with_approval():
    request = {
        "status": "approval_required",
        "requested": ["browser"],
        "unavailable": ["browser"],
        "approval_required": True,
    }
    approval = record_capability_approval(request, "approve").to_dict()

    result = preflight_capability_activation(
        request,
        approval,
        CapabilityManifest(),
        activation_implemented=True,
    )

    assert result.status == "blocked"
    assert result.activation_allowed is False
    assert "browser" in result.reason


def test_ready_when_all_checks_pass_and_activation_exists():
    request = _request()
    approval = record_capability_approval(request, "approve").to_dict()

    result = preflight_capability_activation(
        request,
        approval,
        CapabilityManifest(),
        activation_implemented=True,
    )

    assert result.status == "ready"
    assert result.activation_allowed is True
