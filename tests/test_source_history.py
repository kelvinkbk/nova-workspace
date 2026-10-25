from database.schema import initialize_database
from database.source_repo import seen, set_source, unseen_urls


def test_source_history_remembers_seen_url(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "source.db")
    initialize_database()

    assert not seen("https://example.com/a", "software income")

    set_source("https://example.com/a", "software income", "rejected", "not relevant")

    assert seen("https://example.com/a", "software income")
    assert unseen_urls(
        ["https://example.com/a", "https://example.org/b"],
        "software income",
    ) == ["https://example.org/b"]


def test_same_url_can_be_researched_for_a_different_goal(tmp_path, monkeypatch):
    monkeypatch.setattr("database.connection.DATABASE_PATH", tmp_path / "source2.db")
    initialize_database()

    set_source("https://example.com/a", "software income", "useful")

    assert unseen_urls(
        ["https://example.com/a"],
        "digital products",
    ) == ["https://example.com/a"]
