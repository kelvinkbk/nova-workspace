import pytest

from core.brain import BrainDecision
from core.identity import NovaIdentity
from core.loop import run_continuous
from core.runtime import RuntimeState
from database.memory_repository import load_episodes
from database.schema import initialize_database


class TestBrain:
    def think(self, context):
        return BrainDecision(
            thought="Run the observation action.",
            goal="Test continuous runtime",
            plan=["Execute a safe action."],
            action="record_observation",
            reason="Test loop.",
        )


def test_run_continuous_runs_multiple_cycles(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    monkeypatch.setattr(
        "database.connection.DATABASE_PATH",
        database_path,
    )
    initialize_database()

    identity = NovaIdentity()
    runtime = RuntimeState(brain=TestBrain())
    runtime.start()

    results = run_continuous(
        runtime,
        identity,
        interval_seconds=0,
        max_cycles=2,
    )

    assert len(results) == 2
    assert results[0]["cycle"] == 1
    assert results[1]["cycle"] == 2
    assert runtime.cycle == 2
    assert len(load_episodes()) >= 2


def test_run_continuous_rejects_invalid_interval():
    runtime = RuntimeState(brain=TestBrain())
    runtime.start()
    identity = NovaIdentity()

    with pytest.raises(ValueError):
        run_continuous(runtime, identity, interval_seconds=-1, max_cycles=1)


def test_run_continuous_rejects_invalid_cycle_count():
    runtime = RuntimeState(brain=TestBrain())
    runtime.start()
    identity = NovaIdentity()

    with pytest.raises(ValueError):
        run_continuous(runtime, identity, interval_seconds=0, max_cycles=0)
