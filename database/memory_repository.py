import json

from database.connection import get_connection
from memory.episodic import Episode
from memory.journal import JournalEntry
from memory.working import WorkingMemory


def _ensure_working_memory_schema(connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(working_memory)").fetchall()
    }
    if not columns:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS working_memory (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_goal TEXT,
                current_task TEXT,
                active_project TEXT,
                notes TEXT NOT NULL DEFAULT '[]',
                plan_steps TEXT NOT NULL DEFAULT '[]',
                plan_index INTEGER NOT NULL DEFAULT 0,
                plan_goal TEXT,
                last_action TEXT,
                last_action_result TEXT,
                last_reflection TEXT
            )
            """
        )
        return
    if "opportunity_evidence" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN opportunity_evidence TEXT NOT NULL DEFAULT '[]'")
    if "selected_opportunity" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN selected_opportunity TEXT")
    if "search_queries" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN search_queries TEXT NOT NULL DEFAULT '[]'")
    if "research_updated_at" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN research_updated_at TEXT")
    if "opportunity_synthesis" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN opportunity_synthesis TEXT NOT NULL DEFAULT '[]'")
    if "validation_plan" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN validation_plan TEXT")
    if "build_decision" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN build_decision TEXT")
    if "build_spec" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN build_spec TEXT")
    if "build_plan" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN build_plan TEXT")
    if "plan_steps" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN plan_steps TEXT NOT NULL DEFAULT '[]'")
    if "plan_index" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN plan_index INTEGER NOT NULL DEFAULT 0")
    if "plan_goal" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN plan_goal TEXT")
    if "last_action" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN last_action TEXT")
    if "last_action_result" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN last_action_result TEXT")
    if "last_reflection" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN last_reflection TEXT")


def save_working_memory(memory: WorkingMemory) -> None:
    connection = get_connection()
    _ensure_working_memory_schema(connection)
    connection.execute(
        """
        INSERT INTO working_memory (
            id,
            current_goal,
            current_task,
            active_project,
            notes,
            plan_steps,
            plan_index,
            plan_goal,
            last_action,
            last_action_result,
            last_reflection,
            candidate_urls,
            candidate_index,
            opportunity_evidence,
            selected_opportunity,
            search_queries,
            research_updated_at,
            opportunity_synthesis,
            validation_plan,
            build_decision,
            build_spec,
            build_plan
        )
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            current_goal = excluded.current_goal,
            current_task = excluded.current_task,
            active_project = excluded.active_project,
            notes = excluded.notes,
            plan_steps = excluded.plan_steps,
            plan_index = excluded.plan_index,
            plan_goal = excluded.plan_goal,
            last_action = excluded.last_action,
            last_action_result = excluded.last_action_result,
            last_reflection = excluded.last_reflection,
            candidate_urls = excluded.candidate_urls,
            candidate_index = excluded.candidate_index,
            opportunity_evidence = excluded.opportunity_evidence,
            selected_opportunity = excluded.selected_opportunity,
            search_queries = excluded.search_queries,
            research_updated_at = excluded.research_updated_at,
            opportunity_synthesis = excluded.opportunity_synthesis,
            validation_plan = excluded.validation_plan,
            build_decision = excluded.build_decision,
            build_spec = excluded.build_spec,
            build_plan = excluded.build_plan
        """,
        (
            memory.current_goal,
            memory.current_task,
            memory.active_project,
            json.dumps(memory.notes),
            json.dumps(memory.plan_steps),
            memory.plan_index,
            memory.plan_goal,
            memory.last_action,
            memory.last_action_result,
            memory.last_reflection,
            json.dumps(memory.candidate_urls),
            memory.candidate_index,
            json.dumps(memory.opportunity_evidence),
            json.dumps(memory.selected_opportunity) if memory.selected_opportunity is not None else None,
            json.dumps(memory.search_queries),
            memory.research_updated_at,
            json.dumps(memory.opportunity_synthesis),
            json.dumps(memory.validation_plan) if memory.validation_plan is not None else None,
            json.dumps(memory.build_decision) if memory.build_decision is not None else None,
            json.dumps(memory.build_spec) if memory.build_spec is not None else None,
            json.dumps(memory.build_plan) if memory.build_plan is not None else None,
        ),
    )
    connection.commit()
    connection.close()


def load_working_memory() -> WorkingMemory:
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM working_memory WHERE id = 1"
    ).fetchone()
    connection.close()
    if row is None:
        return WorkingMemory()
    return WorkingMemory(
        current_goal=row["current_goal"],
        current_task=row["current_task"],
        active_project=row["active_project"],
        notes=json.loads(row["notes"]),
        plan_steps=json.loads(row["plan_steps"]),
        plan_index=row["plan_index"],
        plan_goal=row["plan_goal"],
        last_action=row["last_action"],
        last_action_result=row["last_action_result"],
        last_reflection=row["last_reflection"],
        candidate_urls=json.loads(row["candidate_urls"]),
        candidate_index=row["candidate_index"],
        opportunity_evidence=json.loads(row["opportunity_evidence"]),
        selected_opportunity=(
            json.loads(row["selected_opportunity"])
            if row["selected_opportunity"]
            else None
        ),
        search_queries=json.loads(row["search_queries"]),
        research_updated_at=row["research_updated_at"],
        opportunity_synthesis=json.loads(row["opportunity_synthesis"]),
        validation_plan=(
            json.loads(row["validation_plan"])
            if row["validation_plan"]
            else None
        ),
        build_decision=(
            json.loads(row["build_decision"])
            if row["build_decision"]
            else None
        ),
        build_spec=(
            json.loads(row["build_spec"])
            if row["build_spec"]
            else None
        ),
        build_plan=(
            json.loads(row["build_plan"])
            if row["build_plan"]
            else None
        ),
    )


def episode_exists(
    event: str,
    context: str,
    outcome: str,
) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM episodes
            WHERE event = ?
              AND context = ?
              AND outcome = ?
            LIMIT 1
            """,
            (event, context, outcome),
        ).fetchone()
    return row is not None


def save_episode(episode: Episode) -> int | None:
    if episode_exists(
        episode.event,
        episode.context,
        episode.outcome,
    ):
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id
                FROM episodes
                WHERE event = ?
                  AND context = ?
                  AND outcome = ?
                LIMIT 1
                """,
                (
                    episode.event,
                    episode.context,
                    episode.outcome,
                ),
            ).fetchone()
        return row["id"] if row is not None else None
    connection = get_connection()
    cursor = connection.execute(
        """
        INSERT INTO episodes (
            event,
            context,
            outcome,
            importance,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            episode.event,
            episode.context,
            episode.outcome,
            episode.importance,
            episode.created_at,
        ),
    )
    connection.commit()
    episode_id = cursor.lastrowid
    connection.close()
    return episode_id


def load_episodes(limit: int = 50) -> list[Episode]:
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT event, context, outcome, importance, created_at
        FROM episodes
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    connection.close()
    return [
        Episode(
            event=row["event"],
            context=row["context"],
            outcome=row["outcome"],
            importance=row["importance"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def save_journal_entry(entry: JournalEntry) -> int:
    connection = get_connection()
    cursor = connection.execute(
        """
        INSERT INTO journal (
            title,
            content,
            life_day,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            entry.title,
            entry.content,
            entry.life_day,
            entry.created_at,
        ),
    )
    connection.commit()
    entry_id = cursor.lastrowid
    connection.close()
    return entry_id


def load_journal_entries(limit: int = 50) -> list[JournalEntry]:
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT title, content, life_day, created_at
        FROM journal
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    connection.close()
    return [
        JournalEntry(
            title=row["title"],
            content=row["content"],
            life_day=row["life_day"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def search_memory(query: str, limit: int = 5) -> list[dict]:
    query = query.strip()
    if not query:
        return []
    pattern = f"%{query}%"
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                'episode' AS memory_type,
                event AS title,
                context,
                outcome,
                importance,
                created_at
            FROM episodes
            WHERE event LIKE ?
               OR context LIKE ?
               OR outcome LIKE ?
            UNION ALL
            SELECT
                'journal' AS memory_type,
                title,
                content AS context,
                '' AS outcome,
                1 AS importance,
                created_at
            FROM journal
            WHERE title LIKE ?
               OR content LIKE ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
            """,
            (pattern, pattern, pattern, pattern, pattern, limit),
        ).fetchall()
    return [dict(row) for row in rows]
