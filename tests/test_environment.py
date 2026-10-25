from core.capability_manifest import CapabilityManifest
from tools.environment import environment_map
from tools.registry import ToolDefinition, ToolRegistry


def test_environment_map_reports_available_and_unavailable_capabilities():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="test_tool",
            description="Test tool",
            handler=lambda: "ok",
        )
    )
    registry.register(
        ToolDefinition(
            name="web_search",
            description="Search the public web.",
            handler=lambda: "ok",
        )
    )
    result = environment_map(registry)
    assert "AVAILABLE CAPABILITIES:" in result
    assert "- test_tool" in result
    assert "NETWORK:" in result
    assert "public web search is available through web_search" in result
    assert "public HTTP/HTTPS GET is available through http_get" in result
    assert "UNAVAILABLE CAPABILITIES:" in result
    assert "- payments" in result


def test_environment_map_uses_runtime_capability_manifest():
    registry = ToolRegistry()
    manifest = CapabilityManifest(
        read_only_research=False,
        browser=True,
    )

    result = environment_map(registry, manifest)

    assert "- read_only_research: UNAVAILABLE" in result
    assert "- browser: AVAILABLE" in result
