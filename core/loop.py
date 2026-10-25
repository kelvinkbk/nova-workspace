from __future__ import annotations

import time

from core.clock import calculate_life_day
from core.identity import NovaIdentity
from core.result_interpreter import interpret_action_result
from core.runtime import RuntimeState
from database.identity_repository import save_identity
from database.memory_repository import (
    load_episodes,
    load_journal_entries,
    load_working_memory,
)


AVAILABLE_ACTIONS = [
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
]


def run_continuous(
    runtime: RuntimeState,
    identity: NovaIdentity,
    *,
    interval_seconds: float = 5.0,
    max_cycles: int | None = None,
) -> list[dict]:
    """Run NOVA's cognitive cycle repeatedly until stopped or bounded."""
    if interval_seconds < 0:
        raise ValueError("interval_seconds cannot be negative.")
    if max_cycles is not None and max_cycles < 1:
        raise ValueError("max_cycles must be at least 1 when provided.")

    results: list[dict] = []
    cycle_count = 0

    while max_cycles is None or cycle_count < max_cycles:
        identity.life_day = calculate_life_day(identity.created_at)
        save_identity(identity)

        working_memory = load_working_memory()
        episodes = load_episodes(limit=10)
        journal_entries = load_journal_entries(limit=10)

        cycle_actions = AVAILABLE_ACTIONS.copy()
        previous_action = working_memory.last_action
        previous_result = working_memory.last_action_result or ""
        if previous_action and previous_result:
            interpretation = interpret_action_result(
                previous_action,
                previous_result,
                working_memory.current_goal or "",
            )
            if interpretation.suggested_action in cycle_actions and interpretation.suggested_action != previous_action:
                working_memory.current_task = interpretation.summary
                cycle_actions.remove(previous_action)
                cycle_actions.remove(interpretation.suggested_action)
                cycle_actions.insert(0, interpretation.suggested_action)

        result = runtime.run_cycle(
            life_day=identity.life_day,
            identity=identity.to_dict(),
            working_memory=working_memory.to_dict(),
            recent_episodes=[episode.to_dict() for episode in episodes],
            recent_journal=[entry.to_dict() for entry in journal_entries],
            available_actions=cycle_actions,
        )
        results.append(result)
        cycle_count += 1

        if max_cycles is None or cycle_count < max_cycles:
            if interval_seconds > 0:
                time.sleep(interval_seconds)

    return results
