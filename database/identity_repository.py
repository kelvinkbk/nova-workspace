from core.identity import NovaIdentity
from database.connection import get_connection

def save_identity(identity: NovaIdentity) -> None:
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO identity (
            id,
            name,
            version,
            life_day,
            balance,
            owner_funding,
            created_at
        )
        VALUES (1, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            version = excluded.version,
            life_day = excluded.life_day,
            balance = excluded.balance,
            owner_funding = excluded.owner_funding,
            created_at = excluded.created_at
        """,
        (
            identity.name,
            identity.version,
            identity.life_day,
            identity.balance,
            identity.owner_funding,
            identity.created_at,
        ),
    )
    connection.commit()
    connection.close()

def load_identity() -> NovaIdentity | None:
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM identity WHERE id = 1"
    ).fetchone()
    connection.close()
    if row is None:
        return None
    return NovaIdentity(
        name=row["name"],
        version=row["version"],
        life_day=row["life_day"],
        balance=row["balance"],
        owner_funding=row["owner_funding"],
        created_at=row["created_at"],
    )