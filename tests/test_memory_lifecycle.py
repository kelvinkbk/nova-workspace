from database.connection import get_connection
from database.memory_repository import episode_exists
from database.schema import initialize_database


def test_episode_exists(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    monkeypatch.setattr(
        "database.connection.DATABASE_PATH",
        database_path,
    )
    initialize_database()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO episodes
            (event, context, outcome, importance, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Test event",
                "Test context",
                "Test outcome",
                3,
                "2026-10-03T12:00:00+00:00",
            ),
        )
        connection.commit()

    assert episode_exists(
        "Test event",
        "Test context",
        "Test outcome",
    ) is True
