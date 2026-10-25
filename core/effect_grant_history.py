from __future__ import annotations

from datetime import datetime, timezone

MAX_EFFECT_GRANT_HISTORY = 20


def record_effect_grant_event(
    history: list[dict] | None,
    grant,
    lifecycle: dict,
    *,
    event: str,
) -> list[dict]:
    entries = list(history or [])
    entries.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": str(event),
        "status": str(lifecycle.get("status") or ""),
        "valid": bool(lifecycle.get("valid")),
        "can_use": bool(lifecycle.get("can_use")),
        "issues": list(lifecycle.get("issues") or []),
        "effect_id": str(getattr(grant, "effect_id", "") or ""),
        "grant_fingerprint": str(getattr(grant, "grant_fingerprint", "") or ""),
    })
    return entries[-MAX_EFFECT_GRANT_HISTORY:]
