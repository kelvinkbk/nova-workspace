from database.connection import get_connection
from database.source_repo import init_sources


def initialize_database() -> None:
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS identity (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            life_day INTEGER NOT NULL,
            balance REAL NOT NULL,
            owner_funding REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

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
            last_reflection TEXT,
            candidate_urls TEXT NOT NULL DEFAULT '[]',
            candidate_index INTEGER NOT NULL DEFAULT 0,
            opportunity_evidence TEXT NOT NULL DEFAULT '[]',
            selected_opportunity TEXT,
            search_queries TEXT NOT NULL DEFAULT '[]',
            research_updated_at TEXT,
            opportunity_synthesis TEXT NOT NULL DEFAULT '[]',
            validation_plan TEXT,
            build_decision TEXT,
            build_spec TEXT,
            build_plan TEXT
        )
        """
    )

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(working_memory)").fetchall()
    }
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
    if "candidate_urls" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN candidate_urls TEXT NOT NULL DEFAULT '[]'")
    if "candidate_index" not in columns:
        connection.execute("ALTER TABLE working_memory ADD COLUMN candidate_index INTEGER NOT NULL DEFAULT 0")
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

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            context TEXT NOT NULL,
            outcome TEXT NOT NULL,
            importance INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            life_day INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    init_sources()
    connection.commit()
    connection.close()