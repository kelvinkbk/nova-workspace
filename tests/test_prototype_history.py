from core.prototype_history import MAX_HISTORY_ENTRIES, record_prototype_event


def test_record_prototype_event_appends_bounded_entry():
    plan = {}
    record_prototype_event(plan, "repair", "applied", "changed app.py")

    assert len(plan["prototype_history"]) == 1
    assert plan["prototype_history"][0]["event"] == "repair"
    assert plan["prototype_history"][0]["status"] == "applied"
    assert plan["prototype_history"][0]["details"] == "changed app.py"
    assert "timestamp" in plan["prototype_history"][0]


def test_record_prototype_event_keeps_only_recent_entries():
    plan = {}
    for index in range(MAX_HISTORY_ENTRIES + 5):
        record_prototype_event(plan, "test", str(index))

    assert len(plan["prototype_history"]) == MAX_HISTORY_ENTRIES
    assert plan["prototype_history"][0]["status"] == "5"
    assert plan["prototype_history"][-1]["status"] == str(MAX_HISTORY_ENTRIES + 4)


def test_record_prototype_event_truncates_details():
    plan = {}
    record_prototype_event(plan, "test", "failed", "x" * 5000)

    assert len(plan["prototype_history"][0]["details"]) == 1200
