from __future__ import annotations

from core.effect_grant import ScopedEffectGrant, validate_scoped_effect_grant
from core.effect_grant_lifecycle import validate_effect_grant_lifecycle
from core.effect_intent import EffectIntent, validate_effect_intent


MAX_DRY_RUN_OUTBOX = 20


class EffectGateway:
    """Fail-closed gateway for typed effects.

    M101 has a dry-run backend only. No external handler is reachable here.
    """

    def __init__(self) -> None:
        self._outbox: list[dict] = []

    def submit(
        self,
        intent: EffectIntent | None,
        *,
        grant: ScopedEffectGrant | None = None,
        now=None,
        dry_run: bool = True,
    ) -> dict:
        validation = validate_effect_intent(intent, now=now)
        if not validation["valid"]:
            return {
                "status": "rejected",
                "executed": False,
                "side_effects": False,
                "reason": "Effect intent validation failed.",
                "issues": list(validation["issues"]),
            }

        grant_validation = validate_scoped_effect_grant(
            intent,
            grant,
            now=now,
        )
        if grant_validation["valid"]:
            lifecycle = validate_effect_grant_lifecycle(grant, now=now)
            if not lifecycle["valid"] or not lifecycle["can_use"]:
                grant_validation = {
                    "valid": False,
                    "issues": list(lifecycle["issues"])
                    or ["Scoped effect grant is not active."],
                }
        if not grant_validation["valid"]:
            return {
                "status": "rejected",
                "executed": False,
                "side_effects": False,
                "reason": "Scoped effect grant validation failed.",
                "issues": list(grant_validation["issues"]),
            }

        if not dry_run:
            return {
                "status": "blocked",
                "executed": False,
                "side_effects": False,
                "reason": "Live effect execution is unavailable in M101.",
                "issues": [],
            }

        entry = {
            "status": "dry_run",
            "executed": False,
            "side_effects": False,
            "effect_id": intent.effect_id,
            "kind": intent.kind,
            "target": intent.target,
            "intent_fingerprint": intent.intent_fingerprint,
            "reason": "Effect recorded in the dry-run outbox; no external handler was invoked.",
        }
        self._outbox.append(dict(entry))
        if len(self._outbox) > MAX_DRY_RUN_OUTBOX:
            del self._outbox[:-MAX_DRY_RUN_OUTBOX]
        return entry

    def outbox(self) -> list[dict]:
        return [dict(entry) for entry in self._outbox]
