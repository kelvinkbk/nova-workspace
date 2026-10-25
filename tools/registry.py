from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def available_tools(self) -> list[str]:
        return list(self._tools.keys())
