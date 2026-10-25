from core.capability_manifest import CapabilityManifest
from core.capability_request import create_capability_request


def test_unavailable_capability_requires_external_approval():
    result = create_capability_request(
        ["real_world_user_interaction"],
        CapabilityManifest(),
    )

    assert result.status == "approval_required"
    assert result.approval_required is True
    assert result.activation_allowed is False
    assert result.unavailable == ("real_world_user_interaction",)


def test_unknown_capability_is_rejected():
    result = create_capability_request(
        ["root_shell"],
        CapabilityManifest(),
    )

    assert result.status == "rejected"
    assert result.activation_allowed is False
    assert result.unavailable == ("root_shell",)


def test_available_capability_does_not_activate_anything():
    result = create_capability_request(
        ["read_only_research"],
        CapabilityManifest(),
    )

    assert result.status == "already_available"
    assert result.activation_allowed is False
