"""SQLite connection and schema initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from oloids_auto_renamer.utils.paths import get_database_path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS project_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    output_path TEXT NOT NULL,
    naming_pattern TEXT NOT NULL,
    default_tool TEXT,
    is_active INTEGER NOT NULL DEFAULT 0,
    fallback_unsorted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS detection_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    pattern TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rename_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_name TEXT NOT NULL,
    new_name TEXT NOT NULL,
    source_path TEXT NOT NULL,
    destination_path TEXT NOT NULL,
    detected_tool TEXT NOT NULL,
    project_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    undone_at TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


DEFAULT_RULES = [
    ("Kling", r"kling|kwai", 10, 1),
    ("Higgsfield", r"higgsfield|higgs[_ -]?field|higgs", 20, 1),
]

DEFAULT_NAMING_PATTERN = "{mmdd}_{project}_{seq}"


def get_connection(database_path: Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection with row access by name."""
    db_path = database_path or get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path | None = None) -> None:
    """Initialize schema and seed defaults on first launch."""
    connection = get_connection(database_path)
    with connection:
        connection.executescript(SCHEMA_SQL)
        existing_rules = connection.execute("SELECT COUNT(*) FROM detection_rules").fetchone()[0]
        if existing_rules == 0:
            connection.executemany(
                """
                INSERT INTO detection_rules (tool_name, pattern, priority, is_active)
                VALUES (?, ?, ?, ?)
                """,
                DEFAULT_RULES,
            )

        existing_presets = connection.execute("SELECT COUNT(*) FROM project_presets").fetchone()[0]
        if existing_presets == 0:
            connection.execute(
                """
                INSERT INTO project_presets
                (name, output_path, naming_pattern, default_tool, is_active, fallback_unsorted)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "Kling Project",
                    str(Path.home() / "oloids_auto_renamer_exports"),
                    DEFAULT_NAMING_PATTERN,
                    "Kling",
                    1,
                    1,
                ),
            )

        connection.execute(
            """
            INSERT OR IGNORE INTO app_settings (key, value)
            VALUES
                ('watched_folder', ''),
                ('startup_behavior', 'manual'),
                ('notifications_enabled', '1')
            """
        )
    connection.close()
