from datetime import datetime, timedelta, timezone

from memory.working import WorkingMemory
from core.runtime import RuntimeState


def test_research_state_is_fresh_after_touch():
    memory = WorkingMemory(candidate_urls=["https://example.com/a"])
    memory.touch_research_state()

    assert memory.research_updated_at is not None
    assert not memory.research_state_stale()


def test_research_state_with_missing_timestamp_is_stale():
    memory = WorkingMemory(candidate_urls=["https://example.com/a"])

    assert memory.research_state_stale()


def test_research_state_expires_after_age():
    memory = WorkingMemory(candidate_urls=["https://example.com/a"])
    memory.research_updated_at = (
        datetime.now(timezone.utc) - timedelta(hours=3)
    ).isoformat()

    assert memory.research_state_stale(max_age_hours=2)


def test_runtime_discards_stale_candidate_queue():
    memory = WorkingMemory(
        current_goal="software income",
        current_task="Inspect old candidate",
        candidate_urls=["https://example.com/old"],
        candidate_index=0,
        opportunity_evidence=[{"url": "https://example.com/old"}],
        selected_opportunity={"status": "selected", "url": "https://example.com/old"},
        search_queries=["old query"],
    )

    state = RuntimeState()._sanitize_research_state(memory.to_dict())

    assert state["current_goal"] == "software income"
    assert state["candidate_urls"] == []
    assert state["opportunity_evidence"] == []
    assert state["selected_opportunity"] is None
    assert state["search_queries"] == []
    assert "fresh opportunity research" in state["current_task"]
