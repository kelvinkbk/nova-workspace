from datetime import datetime, timezone
from database.connection import get_connection


def init_sources() -> None:
    with get_connection() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS research_sources (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, goal TEXT NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL, UNIQUE(url, goal))")


def set_source(url: str, goal: str, status: str, reason: str = "") -> None:
    if not url.strip() or not goal.strip():
        return
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO research_sources (url, goal, status, reason, updated_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(url, goal) DO UPDATE SET status=excluded.status, reason=excluded.reason, updated_at=excluded.updated_at",
            (url.strip(), goal.strip(), status, reason, datetime.now(timezone.utc).isoformat()),
        )


def seen(url: str, goal: str) -> bool:
    with get_connection() as connection:
        row = connection.execute("SELECT 1 FROM research_sources WHERE url=? AND goal=? LIMIT 1", (url.strip(), goal.strip())).fetchone()
    return row is not None


def unseen_urls(urls: list[str], goal: str) -> list[str]:
    return [url for url in urls if not seen(url, goal)]
