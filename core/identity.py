from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class NovaIdentity:
    name: str = "NOVA"
    version: str = "0.1.0"
    life_day: int = 1
    balance: float = 0.0
    owner_funding: float = 0.0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "life_day": self.life_day,
            "balance": self.balance,
            "owner_funding": self.owner_funding,
            "created_at": self.created_at,
        }