from __future__ import annotations

import re


_GENERIC_TERMS = {
    "become",
    "financially",
    "financial",
    "self",
    "sustaining",
    "sufficiency",
    "freedom",
}


def _goal_terms(goal: str) -> list[str]:
    return [
        term.lower()
        for term in re.findall(r"[a-zA-Z]{4,}", goal or "")
        if term.lower() not in _GENERIC_TERMS
    ][:6]


def build_search_queries(goal: str) -> list[str]:
    terms = _goal_terms(goal)
    core = " ".join(terms) if terms else "legitimate software income"

    return [
        f"{core} software tool monetization free pricing",
        f"{core} SaaS digital product official pricing free tier",
        f"{core} software business community case study revenue",
        f"{core} software service marketplace demand pricing",
        f"{core} developer tool business real example monetization",
    ]


def extract_query(result: str) -> str:
    for line in (result or "").splitlines():
        if line.strip().lower().startswith("query:"):
            return line.split(":", 1)[1].strip()
    return ""


def build_search_query(
    goal: str,
    previous_query: str = "",
    *,
    attempt: int = 0,
) -> str:
    queries = build_search_queries(goal)
    seen = previous_query.strip().lower()
    if seen:
        for query in queries:
            if query.lower() == seen:
                index = queries.index(query)
                return queries[(index + max(1, attempt)) % len(queries)]
    return queries[min(max(0, attempt), len(queries) - 1)]


def next_search_query(goal: str, previous_queries: list[str] | None = None) -> str:
    previous = {str(item).strip().lower() for item in (previous_queries or []) if str(item).strip()}
    for query in build_search_queries(goal):
        if query.lower() not in previous:
            return query
    return build_search_queries(goal)[0]
