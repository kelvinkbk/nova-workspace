from database.connection import get_connection
from database.memory_repository import search_memory
from database.schema import initialize_database


def test_search_memory_prioritizes_importance(tmp_path, monkeypatch):
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
                "Financial opportunity",
                "Low importance financial event",
                "",
                1,
                "2026-10-03T10:00:00+00:00",
            ),
        )
        connection.execute(
            """
            INSERT INTO episodes
            (event, context, outcome, importance, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Financial milestone",
                "High importance financial event",
                "",
                5,
                "2026-10-03T09:00:00+00:00",
            ),
        )
        connection.commit()

    results = search_memory("financial")

    assert len(results) == 2
    assert results[0]["title"] == "Financial milestone"
    assert results[0]["importance"] == 5
