from datetime import datetime, timezone


MAX_HISTORY_ENTRIES = 20


def record_prototype_event(
    build_plan: dict | None,
    event: str,
    status: str,
    details: str = "",
) -> dict:
    plan = build_plan if isinstance(build_plan, dict) else {}
    history = list(plan.get("prototype_history") or [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": str(event).strip() or "unknown",
            "status": str(status).strip() or "unknown",
            "details": str(details).strip()[:1200],
        }
    )
    history = history[-MAX_HISTORY_ENTRIES:]
    plan["prototype_history"] = history
    return plan
