from dataclasses import dataclass

from core.opportunity_evaluator import evaluate_search_results
from core.search_strategy import build_search_query, extract_query


@dataclass(frozen=True)
class ResultInterpretation:
    summary: str
    suggested_action: str | None = None
    suggested_input: dict | None = None


def interpret_action_result(
    action: str,
    result: str,
    goal: str = "",
) -> ResultInterpretation:
    text = result or ""

    if action == "web_search" and text.startswith("[BEGIN UNTRUSTED WEB SEARCH RESULTS]"):
        candidates = evaluate_search_results(text, goal)
        previous_query = extract_query(text)

        weak_topical_result = bool(
            candidates
            and any("weak/non-actionable" in reason for reason in candidates[0].reasons)
        )
        if candidates and not weak_topical_result:
            best = candidates[0]
            return ResultInterpretation(
                summary=(
                    f"Search results were ranked. Best candidate: {best.title} "
                    f"(score={best.score}); inspect it before deciding further."
                ),
                suggested_action="http_get",
                suggested_input={"url": best.url},
            )

        next_query = build_search_query(
            goal,
            previous_query,
            attempt=1 if candidates else 0,
        )
        if candidates:
            summary = (
                f"Search results were too weak for inspection (best score={candidates[0].score}); "
                "run a more evidence-oriented search."
            )
        else:
            summary = (
                "The search produced no structured opportunity candidates; improve the query."
            )
        return ResultInterpretation(
            summary=summary,
            suggested_action="web_search",
            suggested_input={"query": next_query},
        )

    if action == "web_search" and text.startswith("No search results found"):
        next_query = build_search_query(goal, extract_query(text), attempt=1)
        return ResultInterpretation(
            summary="No search results were returned; broaden the search with a more specific earning strategy.",
            suggested_action="web_search",
            suggested_input={"query": next_query},
        )

    if action == "http_get" and text.startswith("Network denied:"):
        next_query = build_search_query(goal, "", attempt=2)
        return ResultInterpretation(
            summary=(
                "The selected source could not be fetched; search for a different "
                "evidence-oriented source."
            ),
            suggested_action="web_search",
            suggested_input={"query": next_query},
        )

    if action == "http_get" and text.startswith("[BEGIN UNTRUSTED WEB CONTENT]"):
        return ResultInterpretation(
            summary="A public source was fetched; use its contents as evidence.",
            suggested_action="record_observation",
            suggested_input={},
        )

    if action == "record_observation":
        return ResultInterpretation(
            summary="The observation was recorded successfully.",
            suggested_action=None,
            suggested_input={},
        )

    if action == "system_status":
        return ResultInterpretation(
            summary="System status was inspected successfully.",
            suggested_action=None,
            suggested_input={},
        )

    if action == "memory_search":
        return ResultInterpretation(
            summary="Stored memories were searched successfully.",
            suggested_action=None,
            suggested_input={},
        )

    if action == "environment_map":
        return ResultInterpretation(
            summary="The available capability map was inspected.",
            suggested_action=None,
            suggested_input={},
        )

    if action == "list_project_files":
        return ResultInterpretation(
            summary="The project file inventory was inspected.",
            suggested_action=None,
            suggested_input={},
        )

    if action == "read_project_file":
        return ResultInterpretation(
            summary="A project file was read successfully.",
            suggested_action=None,
            suggested_input={},
        )

    if action.startswith(("http_get", "web_search")) and text.startswith(
        ("Network request failed:", "Search failed:")
    ):
        return ResultInterpretation(
            summary="The network operation failed; do not treat the failure as useful evidence.",
            suggested_action=None,
            suggested_input={},
        )

    return ResultInterpretation(
        summary="The action completed; evaluate the result before choosing the next step.",
        suggested_action=None,
        suggested_input={},
    )
