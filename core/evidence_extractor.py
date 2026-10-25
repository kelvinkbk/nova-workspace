from dataclasses import asdict, dataclass
import re
from urllib.parse import urlparse


@dataclass(frozen=True)
class OpportunityEvidence:
    url: str
    title: str
    monetization: str
    startup_cost: str
    difficulty: str
    capital_fit: str
    confidence: str
    source_type: str = "unknown"
    source_quality: str = "low"
    quality_score: int = 0
    content_relevance: str = "low"
    relevance_score: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def _first_signal(text: str, signals: tuple[str, ...]) -> str:
    lowered = text.lower()
    for signal in signals:
        if signal in lowered:
            return signal
    return "unknown"


def _source_quality(url: str, text: str) -> tuple[str, str, int]:
    host = (urlparse(url).hostname or "").lower()
    lowered = text.lower()

    if any(host.endswith(domain) for domain in (".gov", ".gov.in", ".edu")):
        return "official_or_educational", "high", 5
    if any(token in host for token in ("docs.", "developer.", "support.", "pricing.")):
        return "official_product", "high", 5
    if any(token in host for token in ("github.com", "gitlab.com")):
        return "developer_repository", "high", 4
    if any(token in host for token in ("reddit.com", "news.ycombinator.com", "stackoverflow.com")):
        return "community", "medium", 3
    if any(token in host for token in ("producthunt.com", "indiehackers.com", "gumroad.com", "appsumo.com")):
        return "marketplace_or_builder", "medium", 3
    if any(token in lowered for token in ("case study", "customer story", "revenue", "pricing")):
        return "business_article", "medium", 2
    return "general_web", "low", 1


def extract_opportunity_evidence(
    content: str,
    url: str,
    title: str = "",
    goal: str = "",
) -> OpportunityEvidence:
    raw_content = content or ""
    if not title:
        title_match = re.search(
            r"<title[^>]*>(.*?)</title>",
            raw_content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if title_match:
            title = re.sub(r"\s+", " ", title_match.group(1)).strip()
    text = re.sub(r"<[^>]+>", " ", raw_content)
    text = re.sub(r"\s+", " ", text).strip()
    lowered = text.lower()
    host = urlparse(url).hostname or ""

    monetization_signals = (
        "subscription",
        "subscriptions",
        "saas",
        "ads",
        "advertising",
        "affiliate",
        "commission",
        "one-time purchase",
        "digital product",
        "freelance",
        "services",
    )
    monetization = _first_signal(lowered, monetization_signals)

    paid_pattern = re.search(
        r"(?:\$|₹|rs\.?\s*)\s*\d+(?:[.,]\d+)?",
        text,
        flags=re.IGNORECASE,
    )
    free_signal = any(
        phrase in lowered
        for phrase in (
            "free plan",
            "free tier",
            "no upfront cost",
            "no initial investment",
            "start for free",
        )
    )
    if free_signal:
        startup_cost = "explicitly mentions a free/no-upfront option"
        capital_fit = "promising for ₹0 start, subject to actual requirements"
    elif paid_pattern:
        startup_cost = f"price signal found: {paid_pattern.group(0)}"
        capital_fit = "unknown; inspect the actual pricing/requirements"
    else:
        startup_cost = "not stated"
        capital_fit = "unknown"

    difficulty_signal = _first_signal(
        lowered,
        (
            "beginner",
            "easy",
            "simple",
            "no-code",
            "advanced",
            "difficult",
            "technical",
        ),
    )
    difficulty = difficulty_signal if difficulty_signal != "unknown" else "not stated"

    confidence = "medium" if any(
        value != "unknown" and value != "not stated"
        for value in (monetization, startup_cost, difficulty)
    ) else "low"
    source_type, source_quality, quality_score = _source_quality(url, text)

    generic_terms = {"become", "financially", "financial", "self", "sustaining", "sufficiency", "freedom"}
    goal_terms = {
        term.lower()
        for term in re.findall(r"[a-zA-Z]{4,}", goal or "")
        if term.lower() not in generic_terms
    }
    opportunity_terms = (
        "software", "saas", "tool", "developer", "startup", "business",
        "automation", "digital product", "subscription", "affiliate",
        "commission", "services", "freelance", "revenue", "pricing",
    )
    relevance_score = min(4, sum(term in lowered for term in goal_terms))
    relevance_score += min(3, sum(term in lowered for term in opportunity_terms))
    if monetization != "unknown":
        relevance_score += 1
    if free_signal or paid_pattern:
        relevance_score += 1
    relevance_score = max(0, relevance_score)
    if relevance_score >= 5:
        content_relevance = "high"
    elif relevance_score >= 2:
        content_relevance = "medium"
    else:
        content_relevance = "low"

    return OpportunityEvidence(
        url=url,
        title=title or host or "Untitled source",
        monetization=monetization,
        startup_cost=startup_cost,
        difficulty=difficulty,
        capital_fit=capital_fit,
        confidence=confidence,
        source_type=source_type,
        source_quality=source_quality,
        quality_score=quality_score,
        content_relevance=content_relevance,
        relevance_score=relevance_score,
    )
