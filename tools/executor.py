from security.policy import SecurityPolicy
from tools.registry import ToolRegistry


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        policy: SecurityPolicy,
    ) -> None:
        self.registry = registry
        self.policy = policy

    def execute(self, action: str, action_input: dict | None = None) -> str:
        action_input = action_input or {}
        policy_decision = self.policy.evaluate(action)
        if not policy_decision.allowed:
            return (
                f"Action denied: {action}. "
                f"Reason: {policy_decision.reason}"
            )
        tool = self.registry.get(action)
        if tool is None:
            return f"Action denied: {action}. Tool is not registered."
        if action == "memory_search":
            query = action_input.get("query", "")
            if not isinstance(query, str) or not query.strip():
                return "Action denied: memory_search requires a query."
            return tool.handler(query.strip())
        if action == "read_project_file":
            path = action_input.get("path", "")
            if not isinstance(path, str) or not path.strip():
                return "Action denied: read_project_file requires a path."
            return tool.handler(path.strip())
        if action == "http_get":
            url = action_input.get("url", "")
            if not isinstance(url, str) or not url.strip():
                return "Action denied: http_get requires a URL."
            return tool.handler(url.strip())
        if action == "web_search":
            query = action_input.get("query", "")
            if not isinstance(query, str) or not query.strip():
                return "Action denied: web_search requires a query."
            return tool.handler(query.strip())
        if action == "sandbox_write":
            path = action_input.get("path", "")
            content = action_input.get("content", "")
            if not isinstance(path, str) or not path.strip():
                return "Action denied: sandbox_write requires a path."
            if not isinstance(content, str):
                return "Action denied: sandbox_write requires text content."
            return tool.handler(path.strip(), content)
        if action == "sandbox_run_python":
            path = action_input.get("path", "")
            timeout_seconds = action_input.get("timeout_seconds", 10)
            if not isinstance(path, str) or not path.strip():
                return "Action denied: sandbox_run_python requires a path."
            if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
                return "Action denied: sandbox_run_python requires a numeric timeout."
            return tool.handler(path.strip(), float(timeout_seconds))
        if action == "sandbox_build":
            build_plan = action_input.get("build_plan")
            if not isinstance(build_plan, dict):
                return "Action denied: sandbox_build requires a build plan."
            return tool.handler(build_plan)
        if action == "sandbox_run_project_tests":
            project_path = action_input.get("project_path", "")
            timeout_seconds = action_input.get("timeout_seconds", 10)
            if not isinstance(project_path, str) or not project_path.strip():
                return "Action denied: sandbox_run_project_tests requires a project path."
            if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
                return "Action denied: sandbox_run_project_tests requires a numeric timeout."
            return tool.handler(project_path.strip(), float(timeout_seconds))
        return tool.handler()
