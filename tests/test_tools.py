from security.policy import SecurityPolicy
from tools.builtin import record_observation
from tools.executor import ToolExecutor
from tools.filesystem import read_project_file
from tools.search import web_search
from tools.registry import ToolDefinition, ToolRegistry


def create_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="record_observation",
            description="Record the current observation.",
            handler=record_observation,
        )
    )
    return registry


def test_tool_registration():
    registry = create_registry()
    assert "record_observation" in registry.available_tools()
    tool = registry.get("record_observation")
    assert tool is not None
    assert tool.description


def test_allowed_tool_executes():
    registry = create_registry()
    policy = SecurityPolicy()
    executor = ToolExecutor(registry, policy)
    assert executor.execute("record_observation") == "Observation recorded successfully."


def test_unregistered_allowed_tool_is_denied():
    registry = ToolRegistry()
    policy = SecurityPolicy()
    executor = ToolExecutor(registry, policy)
    result = executor.execute("record_observation")
    assert result == "Action denied: record_observation. Tool is not registered."


def test_read_project_file_passes_path_to_tool():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="read_project_file",
            description="Read a project file.",
            handler=read_project_file,
        )
    )
    executor = ToolExecutor(registry, SecurityPolicy())

    result = executor.execute(
        "read_project_file",
        {"path": "README.md"},
    )

    assert isinstance(result, str)
    assert result


def test_web_search_passes_query_to_tool():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="web_search",
            description="Search the web.",
            handler=web_search,
        )
    )
    executor = ToolExecutor(registry, SecurityPolicy())

    result = executor.execute(
        "web_search",
        {"query": "example"},
    )

    assert isinstance(result, str)


def test_dangerous_registered_tool_is_denied():
    executed = False

    def dangerous_handler() -> str:
        nonlocal executed
        executed = True
        return "Dangerous tool executed."

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="transfer_money",
            description="Transfer funds.",
            handler=dangerous_handler,
        )
    )
    executor = ToolExecutor(registry, SecurityPolicy())
    result = executor.execute("transfer_money")
    assert result.startswith("Action denied: transfer_money.")
    assert executed is False
