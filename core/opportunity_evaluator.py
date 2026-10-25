from dataclasses import dataclass
import re
from urllib.parse import urlparse

from core.evidence_extractor import OpportunityEvidence
from core.opportunity_synthesis import consolidated_as_evidence, synthesize_opportunity_evidence


@dataclass(frozen=True)
class OpportunityCandidate:
    title: str
    url: str
    score: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceComparison:
    title: str
    url: str
    score: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class OpportunitySelection:
    status: str
    title: str | None
    url: str | None
    score: int | None
    reasons: tuple[str, ...]
    evidence_count: int


@dataclass(frozen=True)
class OpportunityValidation:
    status: str
    title: str | None
    url: str | None
    reasons: tuple[str, ...]
    required_signals: tuple[str, ...]
    evidence_count: int


_NEGATIVE_SIGNALS = (
    "self-sufficiency",
    "financial freedom",
    "wellness",
    "mindset",
    "blog",
    "lifestyle",
    "motivational",
)

_POSITIVE_SIGNALS = (
    "software",
    "saas",
    "tool",
    "developer",
    "startup",
    "business",
    "automation",
    "template",
    "digital product",
)


def _extract_candidates(search_result: str) -> list[tuple[str, str]]:
    candidates = []
    current_title = None

    for line in search_result.splitlines():
        stripped = line.strip()
        if re.match(r"^\d+\.\s+", stripped):
            current_title = re.sub(r"^\d+\.\s+", "", stripped).strip()
        elif stripped.startswith("URL:") and current_title:
            url = stripped[4:].strip()
            if url.startswith(("http://", "https://")):
                candidates.append((current_title, url))
            current_title = None

    return candidates


def candidate_urls_from_search(search_result: str, goal: str = "") -> list[str]:
    return [candidate.url for candidate in evaluate_search_results(search_result, goal)]


def evaluate_search_results(search_result: str, goal: str) -> list[OpportunityCandidate]:
    goal_terms = {
        term.lower()
        for term in re.findall(r"[a-zA-Z]{4,}", goal or "")
    }
    candidates = []

    for title, url in _extract_candidates(search_result):
        blob = f"{title} {url}".lower()
        score = 0
        reasons = []

        matched_goal = sorted(
            term for term in goal_terms
            if term in blob
        )
        if matched_goal:
            score += min(5, len(matched_goal))
            reasons.append("matches the current goal")

        positive = sorted(
            signal for signal in _POSITIVE_SIGNALS
            if signal in blob
        )
        if positive:
            score += min(5, len(positive))
            reasons.append("contains potentially actionable software/business terms")

        negative = sorted(
            signal for signal in _NEGATIVE_SIGNALS
            if signal in blob
        )
        if negative:
            score -= min(5, len(negative))
            reasons.append("contains weak/non-actionable topical signals")

        host = urlparse(url).hostname or ""
        if host in {"wikipedia.org", "www.wikipedia.org"}:
            score -= 2
            reasons.append("general reference source")

        if not reasons:
            reasons.append("candidate requires inspection")

        candidates.append(
            OpportunityCandidate(
                title=title,
                url=url,
                score=score,
                reasons=tuple(reasons),
            )
        )

    return sorted(
        candidates,
        key=lambda candidate: (candidate.score, candidate.title.lower()),
        reverse=True,
    )


def compare_opportunity_evidence(
    evidence: list[dict | OpportunityEvidence],
    goal: str = "",
) -> list[EvidenceComparison]:
    """Rank inspected opportunities using only explicitly extracted evidence.

    Unknown or unstated fields are neutral; the comparator never invents missing facts.
    """
    goal_terms = {
        term.lower()
        for term in re.findall(r"[a-zA-Z]{4,}", goal or "")
    }
    comparisons = []

    for item in evidence:
        data = item.to_dict() if isinstance(item, OpportunityEvidence) else dict(item)
        title = str(data.get("title") or data.get("url") or "Untitled source")
        url = str(data.get("url") or "")
        score = 0
        reasons = []

        title_blob = f"{title} {url}".lower()
        matched_goal = sorted(term for term in goal_terms if term in title_blob)
        if matched_goal:
            score += min(3, len(matched_goal))
            reasons.append("evidence source matches the current goal")

        startup_cost = str(data.get("startup_cost") or "").lower()
        capital_fit = str(data.get("capital_fit") or "").lower()
        difficulty = str(data.get("difficulty") or "").lower()
        monetization = str(data.get("monetization") or "").lower()
        confidence = str(data.get("confidence") or "").lower()
        quality_score = int(data.get("quality_score") or 0)
        source_quality = str(data.get("source_quality") or "").lower()

        if quality_score > 0:
            bonus = min(3, max(0, quality_score - 1))
            if bonus:
                score += bonus
                reasons.append(f"source quality: {source_quality or 'measured'} (+{bonus})")

        if "free/no-upfront" in startup_cost or "promising for ₹0 start" in capital_fit:
            score += 3
            reasons.append("explicit free/no-upfront option")
        elif "price signal found" in startup_cost:
            reasons.append("pricing was detected; capital fit is still unknown")

        if monetization not in {"unknown", "", "not stated"}:
            score += 2
            reasons.append(f"monetization signal: {monetization}")

        if difficulty in {"beginner", "easy", "simple", "no-code"}:
            score += 2
            reasons.append(f"lower barrier signal: {difficulty}")
        elif difficulty in {"advanced", "difficult", "technical"}:
            score -= 1
            reasons.append(f"higher barrier signal: {difficulty}")

        if confidence == "medium":
            score += 1
            reasons.append("evidence has at least one concrete signal")

        if not reasons:
            reasons.append("insufficient explicit evidence to rank strongly")

        comparisons.append(
            EvidenceComparison(
                title=title,
                url=url,
                score=score,
                reasons=tuple(reasons),
            )
        )

    return sorted(
        comparisons,
        key=lambda candidate: (candidate.score, candidate.title.lower()),
        reverse=True,
    )


def select_best_opportunity(
    evidence: list[dict | OpportunityEvidence],
    goal: str = "",
    *,
    minimum_evidence: int = 2,
) -> OpportunitySelection:
    """Make a conservative selection from inspected evidence.

    A selection is only made when enough sources were inspected and the best
    candidate has positive evidence. Missing/unknown facts never count as proof.
    """
    if len(evidence) < minimum_evidence:
        return OpportunitySelection(
            status="insufficient_evidence",
            title=None,
            url=None,
            score=None,
            reasons=("Inspect more independent candidates before selecting.",),
            evidence_count=len(evidence),
        )

    hosts = {
        (urlparse(str((item.to_dict() if isinstance(item, OpportunityEvidence) else item).get("url") or "")).hostname or "").lower()
        for item in evidence
    }
    hosts.discard("")
    if len(hosts) < 2:
        return OpportunitySelection(
            status="insufficient_source_diversity",
            title=None,
            url=None,
            score=None,
            reasons=("Evidence must come from at least two distinct source domains.",),
            evidence_count=len(evidence),
        )

    ranked = compare_opportunity_evidence(
        consolidated_as_evidence(synthesize_opportunity_evidence(evidence)),
        goal,
    )
    if not ranked:
        return OpportunitySelection(
            status="insufficient_evidence",
            title=None,
            url=None,
            score=None,
            reasons=("No comparable opportunity evidence is available.",),
            evidence_count=len(evidence),
        )

    best = ranked[0]
    if best.score <= 0:
        return OpportunitySelection(
            status="insufficient_evidence",
            title=None,
            url=None,
            score=best.score,
            reasons=(
                "No candidate has enough positive evidence to justify a selection.",
                *best.reasons,
            ),
            evidence_count=len(evidence),
        )

    return OpportunitySelection(
        status="selected",
        title=best.title,
        url=best.url,
        score=best.score,
        reasons=best.reasons,
        evidence_count=len(evidence),
    )


def check_selected_opportunity(selected: dict | None, evidence: list[dict | OpportunityEvidence]) -> OpportunityValidation:
    if not selected or selected.get("status") != "selected":
        return OpportunityValidation("not_selected", None, None, ("No selection exists.",), ("selected opportunity",), len(evidence))

    url = str(selected.get("url") or "")
    matches = []
    for item in evidence:
        data = item.to_dict() if isinstance(item, OpportunityEvidence) else dict(item)
        if str(data.get("url") or "") == url:
            matches.append(data)

    if len(evidence) < 2 or not matches:
        return OpportunityValidation(
            "more_evidence",
            selected.get("title"),
            url or None,
            ("More source evidence is required.",),
            ("multiple sources and selected-source evidence",),
            len(evidence),
        )

    data = matches[-1]
    monetization = str(data.get("monetization") or "").lower()
    startup_cost = str(data.get("startup_cost") or "").lower()
    capital_fit = str(data.get("capital_fit") or "").lower()
    confidence = str(data.get("confidence") or "").lower()

    missing = []
    reasons = []
    if monetization in {"", "unknown", "not stated"}:
        missing.append("monetization")
    else:
        reasons.append("monetization is explicit")

    zero_ok = "free/no-upfront" in startup_cost or ("promising for" in capital_fit and "zero start" in capital_fit)
    if zero_ok:
        reasons.append("startup signal is compatible with a zero-cost start")
    else:
        missing.append("zero-cost-compatible startup signal")

    if confidence == "medium":
        reasons.append("evidence confidence is medium")
    else:
        missing.append("medium confidence")

    if missing:
        return OpportunityValidation(
            "more_evidence",
            selected.get("title"),
            url or None,
            tuple(reasons + ["Missing: " + ", ".join(missing)]),
            tuple(missing),
            len(evidence),
        )

    return OpportunityValidation(
        "validated",
        selected.get("title"),
        url or None,
        tuple(reasons),
        ("monetization", "zero-cost-compatible startup", "medium confidence"),
        len(evidence),
    )


def summarize_evidence_comparison(
    evidence: list[dict | OpportunityEvidence],
    goal: str = "",
) -> str:
    ranked = compare_opportunity_evidence(evidence, goal)
    if not ranked:
        return "No inspected opportunity evidence is available for comparison."

    best = ranked[0]
    return (
        f"Evidence comparison: strongest inspected candidate is {best.title} "
        f"| score={best.score} | reasons={', '.join(best.reasons)}"
    )


def summarize_best_candidate(search_result: str, goal: str) -> str:
    candidates = evaluate_search_results(search_result, goal)
    if not candidates:
        return "No structured opportunity candidates were found in the search results."

    best = candidates[0]
    return (
        f"Best candidate: {best.title} | score={best.score} | "
        f"reasons={', '.join(best.reasons)}"
    )
