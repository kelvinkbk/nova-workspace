from core.capability_manifest import CapabilityManifest
from core.capability_request_controller import build_and_store_capability_request


def test_new_request_clears_old_approval():
    build_plan = {}
    first = build_and_store_capability_request(
        build_plan,
        ["real_world_user_interaction"],
        CapabilityManifest(),
    )

    build_plan["capability_approval"] = {
        "status": "approved_pending_activation",
        "requested": ["real_world_user_interaction"],
        "activation_allowed": False,
        "request_fingerprint": "old",
    }

    second = build_and_store_capability_request(
        build_plan,
        ["browser"],
        CapabilityManifest(),
    )

    assert first != second
    assert "capability_approval" not in build_plan
    assert "capability_approval_integrity" not in build_plan
    assert build_plan["previous_capability_approval"]["status"] == "superseded"
    assert build_plan["capability_request"] == second


def test_same_request_does_not_clear_existing_approval():
    build_plan = {}
    request = build_and_store_capability_request(
        build_plan,
        ["real_world_user_interaction"],
        CapabilityManifest(),
    )

    build_plan["capability_approval"] = {
        "status": "approved_pending_activation",
        "requested": ["real_world_user_interaction"],
        "activation_allowed": False,
    }

    again = build_and_store_capability_request(
        build_plan,
        ["real_world_user_interaction"],
        CapabilityManifest(),
    )

    assert again == request
    assert build_plan["capability_approval"]["status"] == "approved_pending_activation"
