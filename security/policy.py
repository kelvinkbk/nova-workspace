from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    allowed: bool
    reason: str


class SecurityPolicy:
    """
    Immutable runtime policy boundary.

    The brain can request an action, but it cannot change the policy that
    determines whether that action is allowed.
    """

    _ALLOWED_ACTIONS = frozenset(
        {
            "record_observation",
            "system_status",
            "finance_status",
            "memory_search",
            "environment_map",
            "list_project_files",
            "read_project_file",
            "http_get",
            "web_search",
            "sandbox_write",
            "sandbox_run_python",
            "sandbox_build",
            "sandbox_run_project_tests",
        }
    )

    def evaluate(self, action: str) -> PolicyDecision:
        if action in self._ALLOWED_ACTIONS:
            return PolicyDecision(
                action=action,
                allowed=True,
                reason="Action is explicitly permitted by policy.",
            )
        return PolicyDecision(
            action=action,
            allowed=False,
            reason="Action is not permitted by the current security policy.",
        )
