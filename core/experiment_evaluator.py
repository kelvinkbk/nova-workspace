from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExperimentEvaluation:
    status: str
    signal_strength: str
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "signal_strength": self.signal_strength,
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
        }


def evaluate_experiment_result(result: str) -> ExperimentEvaluation:
    text = str(result or "").strip()

    if text.startswith(("Search failed:", "Action denied:", "Network denied:", "Network request failed:")):
        return ExperimentEvaluation(
            status="blocked",
            signal_strength="none",
            blockers=["The bounded evidence search did not complete successfully."],
        )

    if not text.startswith("[BEGIN UNTRUSTED WEB SEARCH RESULTS]"):
        return ExperimentEvaluation(
            status="inconclusive",
            signal_strength="none",
            blockers=["No trusted experiment result format was recorded."],
        )

    body = text.lower()
    result_markers = (
        "1. ",
        "2. ",
        "url:",
    )
    result_count = sum(marker in body for marker in result_markers)

    demand_terms = (
        "customers",
        "users",
        "demand",
        "pricing",
        "revenue",
        "market",
        "paid",
        "subscription",
    )
    demand_hits = sum(term in body for term in demand_terms)

    reasons = [
        f"Bounded search returned approximately {result_count} structured result markers.",
    ]

    if demand_hits >= 3 and result_count >= 2:
        reasons.append(
            "The search contains multiple demand or monetization signals."
        )
        return ExperimentEvaluation(
            status="evidence_found",
            signal_strength="moderate",
            reasons=reasons,
        )

    if result_count >= 1:
        reasons.append(
            "The search returned usable external evidence, but it is not enough to establish demand conclusively."
        )
        return ExperimentEvaluation(
            status="inconclusive",
            signal_strength="weak",
            reasons=reasons,
            blockers=["Real-world user demand is not established by search results alone."],
        )

    return ExperimentEvaluation(
        status="inconclusive",
        signal_strength="none",
        reasons=reasons,
        blockers=["No structured search results were detected."],
    )
