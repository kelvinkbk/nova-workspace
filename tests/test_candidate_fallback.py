from core.brain import BrainDecision
from core.identity import NovaIdentity
from core.runtime import RuntimeState
from database.memory_repository import save_working_memory
from database.schema import initialize_database
from memory.working import WorkingMemory


def test_candidate_queue_stores_ranked_urls():
    runtime = RuntimeState()
    memory = WorkingMemory(
        current_goal="software income",
    )
    decision = BrainDecision(
        thought="Search.",
        goal="software income",
        plan=["Search", "Inspect candidates"],
        action="web_search",
        reason="Find opportunities.",
        action_input={"query": "software income"},
    )
    result = """[BEGIN UNTRUSTED WEB SEARCH RESULTS]
1. SaaS Tool
   URL: https://example.com/saas
2. Developer Business
   URL: https://example.com/developer
[END UNTRUSTED WEB SEARCH RESULTS]"""

    runtime.update_candidate_queue(memory, decision, result)

    assert memory.candidate_urls == [
        "https://example.com/saas",
        "https://example.com/developer",
    ]
    assert memory.candidate_index == 0
    assert "candidate 1 of 2" in memory.current_task


def test_candidate_queue_falls_forward_after_failed_fetch():
    runtime = RuntimeState()
    memory = WorkingMemory(
        current_goal="software income",
        candidate_urls=[
            "https://example.com/one",
            "https://example.com/two",
        ],
        candidate_index=0,
    )
    decision = BrainDecision(
        thought="Inspect first.",
        goal="software income",
        plan=["Inspect candidates"],
        action="http_get",
        reason="Inspect source.",
        action_input={"url": memory.candidate_urls[0]},
    )

    runtime.update_candidate_queue(
        memory,
        decision,
        "Network request failed: HTTP 403",
    )

    assert memory.candidate_index == 1
    assert memory.current_task == "Inspect ranked opportunity candidate 2 of 2"


def test_candidate_queue_exhaustion_sets_comparison_task():
    runtime = RuntimeState()
    memory = WorkingMemory(
        current_goal="software income",
        candidate_urls=["https://example.com/one"],
        candidate_index=0,
    )
    decision = BrainDecision(
        thought="Inspect.",
        goal="software income",
        plan=["Inspect"],
        action="http_get",
        reason="Inspect source.",
        action_input={"url": memory.candidate_urls[0]},
    )

    runtime.update_candidate_queue(
        memory,
        decision,
        "[BEGIN UNTRUSTED WEB CONTENT]source[END UNTRUSTED WEB CONTENT]",
    )

    assert memory.candidate_index == 1
    assert memory.current_task == "Compare the inspected opportunity candidates"
