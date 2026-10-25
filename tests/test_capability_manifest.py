from core.capability_manifest import CapabilityManifest


def test_default_manifest_is_conservative():
    manifest = CapabilityManifest()

    assert manifest.read_only_research is True
    assert manifest.sandbox_mutation is True
    assert manifest.real_world_user_interaction is False
    assert manifest.financial_accounts is False
    assert manifest.payments is False


def test_manifest_reports_unknown_capability_as_unavailable():
    manifest = CapabilityManifest()

    assert manifest.available("not_a_real_capability") is False


def test_manifest_lists_unavailable_capabilities():
    manifest = CapabilityManifest()

    unavailable = manifest.unavailable()

    assert "real_world_user_interaction" in unavailable
    assert "financial_accounts" in unavailable
    assert "payments" in unavailable
