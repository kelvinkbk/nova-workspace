from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentControl:
    status: str
    action: str | None
    action_input: dict
    reason: str

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "action": self.action,
            "action_input": dict(self.action_input),
            "reason": self.reason,
        }


def choose_experiment_action(
    experiment: dict | None,
    available_actions: list[str] | None = None,
) -> ExperimentControl:
    plan = experiment if isinstance(experiment, dict) else {}
    actions = set(available_actions or [])

    if plan.get("status") != "ready":
        return ExperimentControl(
            status="blocked",
            action=None,
            action_input={},
            reason="Experiment is not in the ready state.",
        )

    if "web_search" not in actions:
        return ExperimentControl(
            status="blocked",
            action=None,
            action_input={},
            reason="A permitted read-only web_search capability is required for this experiment.",
        )

    title = str(plan.get("title") or "next experiment").strip()
    hypothesis = str(plan.get("hypothesis") or "").strip()
    query = f"{title} {hypothesis} evidence demand validation"
    query = " ".join(query.split())[:300]

    return ExperimentControl(
        status="ready",
        action="web_search",
        action_input={"query": query},
        reason=(
            "Run exactly one bounded read-only evidence search for the next experiment; "
            "do not modify or deploy the completed prototype."
        ),
    )


def record_experiment_result(
    experiment: dict | None,
    action: str,
    result: str,
) -> dict:
    plan = dict(experiment or {})
    text = str(result or "")
    successful = not text.startswith(
        ("Search failed:", "Network denied:", "Network request failed:", "Action denied:")
    )

    plan["result"] = text[:1200]
    plan["action"] = action
    plan["status"] = "completed" if successful else "blocked"
    plan["completion_reason"] = (
        "One bounded evidence step completed."
        if successful
        else "The bounded evidence step failed; no prototype mutation is permitted."
    )
    return plan
