from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Episode:
    event: str
    context: str = ""
    outcome: str = ""
    importance: int = 1
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event": self.event,
            "context": self.context,
            "outcome": self.outcome,
            "importance": self.importance,
            "created_at": self.created_at,
        }
