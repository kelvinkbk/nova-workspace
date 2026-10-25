from dataclasses import dataclass
import re
from urllib.parse import urlparse

from core.evidence_extractor import OpportunityEvidence

@dataclass(frozen=True)
class ConsolidatedOpportunity:
    key: str
    title: str
    urls: tuple[str, ...]
    source_count: int
    monetization: str
    startup_cost: str
    difficulty: str
    capital_fit: str
    confidence: str
    quality_score: int
    relevance_score: int
    field_sources: dict[str, tuple[str, ...]]

    def to_dict(self) -> dict:
        return {
            "key": self.key, "title": self.title, "urls": list(self.urls),
            "source_count": self.source_count, "monetization": self.monetization,
            "startup_cost": self.startup_cost, "difficulty": self.difficulty,
            "capital_fit": self.capital_fit, "confidence": self.confidence,
            "quality_score": self.quality_score, "relevance_score": self.relevance_score,
            "field_sources": {k: list(v) for k, v in self.field_sources.items()},
        }

_STOPWORDS = {"the", "and", "for", "with", "from", "your", "this", "that", "free", "guide", "best", "how", "ways", "business", "software"}

def _key_for(item: dict | OpportunityEvidence) -> str:
    data = item.to_dict() if isinstance(item, OpportunityEvidence) else dict(item)
    title = str(data.get("title") or "").lower()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    terms = [x for x in title.split() if len(x) >= 3 and x not in _STOPWORDS]
    if terms:
        return " ".join(sorted(set(terms)))
    host = (urlparse(str(data.get("url") or "")).hostname or "").lower()
    return host or "unknown-opportunity"

def _merge_field(items: list[dict], field: str) -> tuple[str, tuple[str, ...]]:
    usable = [item for item in items if str(item.get(field) or "").lower() not in {"", "unknown", "not stated"}]
    if not usable:
        return "unknown" if field != "difficulty" else "not stated", ()
    usable.sort(key=lambda item: int(item.get("quality_score") or 0), reverse=True)
    value = str(usable[0].get(field))
    sources = tuple(str(item.get("url") or "") for item in usable if item.get("url"))
    return value, sources

def consolidated_as_evidence(items: list[ConsolidatedOpportunity]) -> list[dict]:
    return [
        {
            "title": item.title,
            "url": item.urls[0] if item.urls else "",
            "monetization": item.monetization,
            "startup_cost": item.startup_cost,
            "difficulty": item.difficulty,
            "capital_fit": item.capital_fit,
            "confidence": item.confidence,
            "quality_score": item.quality_score,
            "relevance_score": item.relevance_score,
            "source_count": item.source_count,
        }
        for item in items
    ]


def synthesize_opportunity_evidence(evidence: list[dict | OpportunityEvidence]) -> list[ConsolidatedOpportunity]:
    groups: dict[str, list[dict]] = {}
    for item in evidence:
        data = item.to_dict() if isinstance(item, OpportunityEvidence) else dict(item)
        groups.setdefault(_key_for(data), []).append(data)

    results = []
    for key, items in groups.items():
        urls = tuple(str(item.get("url") or "") for item in items if item.get("url"))
        title = str(items[0].get("title") or items[0].get("url") or "Untitled source")
        fields = {}
        values = {}
        for field in ("monetization", "startup_cost", "difficulty", "capital_fit", "confidence"):
            values[field], fields[field] = _merge_field(items, field)
        results.append(ConsolidatedOpportunity(
            key=key, title=title, urls=urls, source_count=len(items),
            monetization=values["monetization"], startup_cost=values["startup_cost"],
            difficulty=values["difficulty"], capital_fit=values["capital_fit"],
            confidence=values["confidence"],
            quality_score=max((int(item.get("quality_score") or 0) for item in items), default=0),
            relevance_score=max((int(item.get("relevance_score") or 0) for item in items), default=0),
            field_sources=fields,
        ))
    return sorted(results, key=lambda item: (item.source_count, item.quality_score, item.relevance_score, item.title.lower()), reverse=True)