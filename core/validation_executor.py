from dataclasses import dataclass


_FAILURE_PREFIXES = (
    "Action denied:",
    "Network request failed:",
    "Network denied:",
    "Search failed:",
    "File read failed:",
    "File not found:",
)


@dataclass(frozen=True)
class ValidationAction:
    status: str
    step_index: int
    action: str | None
    action_input: dict
    reason: str


def _title(plan: dict) -> str:
    return str(plan.get("title") or "selected opportunity").strip()


def choose_validation_action(plan: dict | None) -> ValidationAction:
    if not isinstance(plan, dict):
        return ValidationAction("inactive", 0, None, {}, "No validation plan is active.")

    status = str(plan.get("status") or "ready")
    index = int(plan.get("step_index") or 0)
    title = _title(plan)

    if status == "blocked":
        return ValidationAction(
            "blocked",
            index,
            "record_observation",
            {},
            "Real-world validation requires capabilities that are not currently available.",
        )

    actions = (
        (
            "memory_search",
            {"query": f"{title} user problem demand"},
            "Check NOVA's existing memory for prior demand/problem evidence.",
        ),
        (
            "web_search",
            {"query": f"{title} user demand problem people need"},
            "Search for independent evidence of a real user problem and demand.",
        ),
        (
            "web_search",
            {"query": f"{title} pricing alternatives customers"},
            "Search for pricing and alternative evidence around the smallest product/service test.",
        ),
        (
            "web_search",
            {"query": f"{title} free distribution communities marketplace"},
            "Search for a zero-cost distribution path and measurable acquisition signal.",
        ),
    )

    if index >= len(actions):
        return ValidationAction(
            "blocked",
            index,
            "record_observation",
            {},
            "The research-only validation steps are complete; a real-world test needs capabilities not currently available.",
        )

    action, action_input, reason = actions[index]
    return ValidationAction("ready", index, action, action_input, reason)


def advance_validation_plan(
    plan: dict | None,
    action: str,
    action_result: str,
) -> dict | None:
    if not isinstance(plan, dict):
        return None

    updated = dict(plan)
    updated.setdefault("step_index", 0)
    updated.setdefault("observations", [])
    status = str(updated.get("status") or "ready")
    updated["status"] = status
    if status == "blocked":
        return updated

    if action not in {"memory_search", "web_search"}:
        return updated
    if action_result.startswith(_FAILURE_PREFIXES):
        updated["last_result"] = action_result[:500]
        updated["status"] = "ready"
        return updated

    step_index = int(updated.get("step_index") or 0)
    observations = list(updated.get("observations") or [])
    observations.append(
        {
            "step_index": step_index,
            "action": action,
            "result": action_result[:1000],
        }
    )
    updated["observations"] = observations[-10:]
    updated["step_index"] = step_index + 1

    if updated["step_index"] >= 4:
        updated["status"] = "blocked"
        updated["blocker"] = (
            "Research-only validation is complete. A real-world test requires "
            "additional capabilities not currently enabled."
        )
    else:
        updated["status"] = "ready"

    return updated
