from dataclasses import dataclass, field
from urllib.parse import urlparse
import re


_URL_PATTERN = re.compile(r"URL:\s*(https?://[^\s]+)", re.IGNORECASE)


@dataclass(frozen=True)
class ExperimentDecision:
    status: str
    confidence: str
    source_domains: tuple[str, ...] = ()
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    next_action: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "confidence": self.confidence,
            "source_domains": list(self.source_domains),
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "next_action": self.next_action,
        }


def _domains(result: str) -> tuple[str, ...]:
    domains = []
    for url in _URL_PATTERN.findall(str(result or "")):
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if host and host not in domains:
            domains.append(host)
    return tuple(domains)


def decide_experiment_outcome(
    initial_experiment: dict | None,
    followup_experiment: dict | None,
) -> ExperimentDecision:
    initial = initial_experiment if isinstance(initial_experiment, dict) else {}
    followup = followup_experiment if isinstance(followup_experiment, dict) else {}

    initial_eval = initial.get("evaluation") if isinstance(initial.get("evaluation"), dict) else {}
    followup_eval = followup.get("evaluation") if isinstance(followup.get("evaluation"), dict) else {}

    domains = list(dict.fromkeys(_domains(initial.get("result", "")) + _domains(followup.get("result", ""))))
    initial_status = str(initial_eval.get("status") or "inconclusive")
    followup_status = str(followup_eval.get("status") or "inconclusive")

    reasons: list[str] = []
    blockers: list[str] = []

    if initial_status == "blocked" or followup_status == "blocked":
        return ExperimentDecision(
            status="blocked",
            confidence="none",
            source_domains=tuple(domains),
            blockers=["At least one bounded evidence experiment failed."],
            next_action="Reassess the research path without mutating the frozen prototype.",
        )

    if initial_status == "evidence_found" and followup_status == "evidence_found":
        if len(domains) >= 2:
            return ExperimentDecision(
                status="corroborated_signal",
                confidence="moderate",
                source_domains=tuple(domains),
                reasons=[
                    "Both bounded experiments produced evidence signals.",
                    "The evidence came from at least two distinct source domains.",
                ],
                next_action=(
                    "Use the corroborated signal as research evidence only; "
                    "perform a separate real-world demand test before spending or deployment."
                ),
            )
        blockers.append("Both searches used the same source domain or did not expose two distinct domains.")
        reasons.append("Both bounded experiments produced evidence signals.")
        return ExperimentDecision(
            status="mixed_signal",
            confidence="low",
            source_domains=tuple(domains),
            reasons=reasons,
            blockers=blockers,
            next_action="Collect independent evidence from another source domain.",
        )

    if initial_status == "evidence_found" or followup_status == "evidence_found":
        return ExperimentDecision(
            status="mixed_signal",
            confidence="low",
            source_domains=tuple(domains),
            reasons=["Only one of the two bounded experiments produced a moderate evidence signal."],
            blockers=["The evidence is not sufficiently consistent to treat the signal as corroborated."],
            next_action="Keep the prototype frozen and gather another independent signal later.",
        )

    return ExperimentDecision(
        status="inconclusive",
        confidence="low",
        source_domains=tuple(domains),
        blockers=["Neither bounded experiment established a corroborated evidence signal."],
        next_action="Keep the prototype frozen and reassess the opportunity.",
    )
