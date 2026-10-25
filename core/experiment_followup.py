from dataclasses import dataclass


@dataclass(frozen=True)
class FollowupExperiment:
    status: str
    title: str
    purpose: str
    query: str
    constraints: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "title": self.title,
            "purpose": self.purpose,
            "query": self.query,
            "constraints": list(self.constraints),
        }


def create_followup_experiment(
    experiment: dict | None,
    evaluation: dict | None,
    followup_count: int = 0,
) -> FollowupExperiment | None:
    plan = experiment if isinstance(experiment, dict) else {}
    result = evaluation if isinstance(evaluation, dict) else {}

    if plan.get("status") != "completed":
        return None
    if followup_count >= 1:
        return None

    title = str(plan.get("title") or "completed experiment").strip()
    status = str(result.get("status") or "inconclusive").strip()
    if status == "evidence_found":
        purpose = "Seek one independent corroborating source before treating the signal as strong evidence."
        query = f"{title} independent evidence customers pricing revenue case study"
    elif status == "inconclusive":
        purpose = "Run one alternate evidence search targeting the unresolved demand assumption."
        query = f"{title} alternative evidence demand users pricing real example"
    else:
        purpose = "Retry the bounded evidence search once using a narrower query."
        query = f"{title} validated demand evidence"

    return FollowupExperiment(
        status="ready",
        title=f"Follow-up experiment for {title}",
        purpose=purpose,
        query=" ".join(query.split())[:300],
        constraints=(
            "At most one follow-up experiment.",
            "Read-only web search only.",
            "Do not modify the completed prototype.",
            "Rs 0 owner funding.",
            "Do not claim demand from search evidence alone.",
        ),
    )
