from datetime import datetime, timezone


MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY = 20


def record_real_world_validation_approval_binding(
    build_plan: dict,
    binding: dict,
) -> dict:
    """Append a bounded audit record for a validation/approval binding decision."""
    if not isinstance(build_plan, dict):
        return binding

    history = build_plan.setdefault(
        "real_world_validation_approval_binding_history",
        [],
    )
    if not isinstance(history, list):
        history = []
        build_plan["real_world_validation_approval_binding_history"] = history

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "valid": bool(binding.get("valid")),
        "issues": list(binding.get("issues") or []),
        "enforcement_status": str(binding.get("enforcement_status") or ""),
        "enforcement_reason": str(binding.get("enforcement_reason") or ""),
    }
    history.append(entry)

    if len(history) > MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY:
        del history[:-MAX_REAL_WORLD_VALIDATION_APPROVAL_BINDING_HISTORY]

    return entry


def real_world_validation_approval_binding_history(
    build_plan: dict,
) -> list[dict]:
    if not isinstance(build_plan, dict):
        return []
    history = build_plan.get("real_world_validation_approval_binding_history")
    if not isinstance(history, list):
        return []
    return [item for item in history if isinstance(item, dict)]
