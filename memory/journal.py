from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class JournalEntry:
    title: str
    content: str
    life_day: int
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "life_day": self.life_day,
            "created_at": self.created_at,
        }
