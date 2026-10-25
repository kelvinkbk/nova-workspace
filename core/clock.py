from datetime import datetime, timezone


def current_utc_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def calculate_life_day(created_at: str) -> int:
    created_date = datetime.fromisoformat(created_at).date()
    today = datetime.now(timezone.utc).date()
    return max(1, (today - created_date).days + 1)
