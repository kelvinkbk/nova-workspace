from __future__ import annotations

import argparse

from core.brain import NovaBrain
from core.identity import NovaIdentity
from core.loop import AVAILABLE_ACTIONS, run_continuous
from core.providers.local_llama import LocalLlamaProvider
from core.runtime import RuntimeState
from database.identity_repository import load_identity, save_identity
from database.memory_repository import (
    load_episodes,
    load_journal_entries,
    load_working_memory,
    save_episode,
    save_journal_entry,
)
from database.schema import initialize_database
from memory.episodic import Episode
from memory.journal import JournalEntry
from memory.working import WorkingMemory
from core.clock import calculate_life_day


def start_nova() -> tuple[
    NovaIdentity,
    WorkingMemory,
    list[Episode],
    list[JournalEntry],
]:
    initialize_database()
    identity = load_identity()
    if identity is None:
        identity = NovaIdentity()
        save_identity(identity)
    identity.life_day = calculate_life_day(identity.created_at)
    save_identity(identity)
    working_memory = load_working_memory()
    episodes = load_episodes(limit=10)
    journal_entries = load_journal_entries(limit=10)
    return identity, working_memory, episodes, journal_entries


def record_startup(identity: NovaIdentity) -> None:
    episode = Episode(
        event="NOVA started",
        context="NOVA runtime startup",
        outcome="Persistent state loaded successfully",
        importance=3,
    )
    save_episode(episode)
    journal_entry = JournalEntry(
        title=f"Life day {identity.life_day}",
        content=(
            "NOVA started successfully. "
            "Persistent identity, working memory, "
            "episodic memory, and journal were loaded."
        ),
        life_day=identity.life_day,
    )
    save_journal_entry(journal_entry)


def print_header(identity: NovaIdentity, working_memory: WorkingMemory) -> None:
    print()
    print("╔══════════════════════════════════════╗")
    print("║              NOVA                    ║")
    print("║       Autonomous AI Workspace        ║")
    print("╚══════════════════════════════════════╝")
    print()
    print("Status: ONLINE")
    print(f"Version: {identity.version}")
    print(f"Life day: {identity.life_day}")
    print(f"Balance: ₹{identity.balance:.2f}")
    print(f"Owner funding: ₹{identity.owner_funding:.2f}")
    print()
    print("── MEMORY ─────────────────────────────")
    print(f"Goal: {working_memory.current_goal}")
    print(f"Task: {working_memory.current_task}")
    print(f"Project: {working_memory.active_project}")


def print_cycle(cycle: dict) -> None:
    print()
    print("── COGNITIVE CYCLE ───────────────────")
    print(f"Cycle: {cycle['cycle']}")
    print(f"Observation: {cycle['observation']}")
    print(f"Thought: {cycle['thought']}")
    print(f"Goal: {cycle['goal']}")
    print(f"Decision: {cycle['decision']}")
    print(f"Policy allowed: {cycle['policy_allowed']}")
    print(f"Policy reason: {cycle['policy_reason']}")
    print(f"Action: {cycle['action']}")
    print(f"Reflection: {cycle['reflection']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the NOVA autonomous runtime.")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run cognitive cycles continuously until Ctrl+C.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Run a bounded number of cycles (default: 1).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Seconds between cycles in continuous/bounded mode (default: 5).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.cycles < 1:
        raise SystemExit("--cycles must be at least 1.")
    if args.interval < 0:
        raise SystemExit("--interval cannot be negative.")

    identity, working_memory, episodes, journal_entries = start_nova()
    record_startup(identity)

    provider = LocalLlamaProvider()
    brain = NovaBrain(provider=provider)
    runtime = RuntimeState(brain=brain)
    runtime.start()
    working_memory = load_working_memory()

    print_header(identity, working_memory)
    print(f"Recent episodes loaded: {len(episodes)}")
    print(f"Journal entries loaded: {len(journal_entries)}")

    try:
        if args.continuous:
            results = run_continuous(
                runtime,
                identity,
                interval_seconds=args.interval,
            )
            for result in results:
                print_cycle(result)
        else:
            results = run_continuous(
                runtime,
                identity,
                interval_seconds=args.interval,
                max_cycles=args.cycles,
            )
            for result in results:
                print_cycle(result)
    except KeyboardInterrupt:
        print()
        print("NOVA shutdown requested.")
    finally:
        runtime.stop()

    print()
    print("Memory: ONLINE")
    print("Database: ONLINE")
    print("Runtime: OFFLINE")
    print("Security: ACTIVE")


if __name__ == "__main__":
    main()
