from tools.registry import ToolRegistry
from core.capability_manifest import CapabilityManifest


def environment_map(registry: ToolRegistry, manifest: CapabilityManifest | None = None) -> str:
    available = registry.available_tools()
    lines = [
        "NOVA ENVIRONMENT MAP",
        "",
        "AVAILABLE CAPABILITIES:",
    ]
    for tool in available:
        lines.append(f"- {tool}")
    manifest = manifest or CapabilityManifest()
    lines.extend(
        [
            "",
            "NETWORK:",
            "- finance_status provides read-only, evidence-based revenue/expense totals",
            "- owner funding is kept separate from earned revenue; pending entries are excluded",
            "- public web search is available through web_search",
            "- public HTTP/HTTPS GET is available through http_get",
            "- network writes are blocked",
            "- sandbox file writes are available only inside NOVA's isolated sandbox",
            "- sandbox Python execution is bounded and intended for prototypes/tests",
            "- sandbox_build creates a non-overwriting prototype scaffold only inside the sandbox",
            "- sandbox_run_project_tests runs only the generated test_app.py with bounded time/output",
            "",
            "CAPABILITY MANIFEST:",
            "UNAVAILABLE CAPABILITIES:",
        ]
    )
    for name, enabled in manifest.to_dict().items():
        state = "AVAILABLE" if enabled else "UNAVAILABLE"
        lines.append(f"- {name}: {state}")

    return "\n".join(lines)
