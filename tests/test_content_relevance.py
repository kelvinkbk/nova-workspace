from core.evidence_extractor import extract_opportunity_evidence
from core.runtime import RuntimeState
from memory.working import WorkingMemory
from core.brain import BrainDecision


def test_relevance_rejects_unrelated_page():
    evidence = extract_opportunity_evidence(
        "<title>Example Domain</title> This is only a documentation example page.",
        "https://example.com/",
        goal="Become financially self-sustaining through software income",
    )

    assert evidence.content_relevance == "low"
    assert evidence.relevance_score <= 1


def test_relevance_accepts_opportunity_page():
    evidence = extract_opportunity_evidence(
        "Build a SaaS software tool. Subscription pricing and free plan available for developers.",
        "https://example.org/saas",
        goal="Become financially self-sustaining through software income",
    )

    assert evidence.content_relevance in {"medium", "high"}
    assert evidence.relevance_score >= 2


def test_runtime_does_not_store_low_relevance_evidence():
    runtime = RuntimeState()
    memory = WorkingMemory(current_goal="software income")
    decision = BrainDecision(
        thought="Inspect source",
        goal="software income",
        plan=["Inspect"],
        action="http_get",
        reason="Inspect source",
        action_input={"url": "https://example.com/"},
    )
    result = (
        "[BEGIN UNTRUSTED WEB CONTENT]"
        "<title>Example Domain</title>documentation example"
        "[END UNTRUSTED WEB CONTENT]"
    )

    runtime.extract_and_store_evidence(memory, decision, result)

    assert memory.opportunity_evidence == []
    assert any("Rejected low-relevance source" in note for note in memory.notes)
