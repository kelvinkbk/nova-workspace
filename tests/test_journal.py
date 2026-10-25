from database.memory_repository import (
    load_journal_entries,
    save_journal_entry,
)
from database.schema import initialize_database
from memory.journal import JournalEntry


def test_journal_persistence():
    initialize_database()
    entry = JournalEntry(
        title="NOVA begins",
        content="Today I initialized my persistent workspace.",
        life_day=1,
    )
    entry_id = save_journal_entry(entry)
    assert entry_id is not None
    entries = load_journal_entries()
    assert len(entries) >= 1
    assert entries[0].title == "NOVA begins"
    assert entries[0].life_day == 1
