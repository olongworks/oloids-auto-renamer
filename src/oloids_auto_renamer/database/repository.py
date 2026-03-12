"""Data access helpers for the SQLite-backed application state."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from oloids_auto_renamer.database.connection import get_connection, initialize_database
from oloids_auto_renamer.models.entities import DetectionRule, ProjectPreset, RenameLog


class AppRepository:
    """Repository that owns SQLite CRUD operations."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path
        initialize_database(self.database_path)

    def _connect(self):
        return get_connection(self.database_path)

    def list_projects(self) -> list[ProjectPreset]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, output_path, naming_pattern, default_tool, is_active, fallback_unsorted
                FROM project_presets
                ORDER BY id ASC
                """
            ).fetchall()
        return [
            ProjectPreset(
                id=row["id"],
                name=row["name"],
                output_path=row["output_path"],
                naming_pattern=row["naming_pattern"],
                default_tool=row["default_tool"],
                is_active=bool(row["is_active"]),
                fallback_unsorted=bool(row["fallback_unsorted"]),
            )
            for row in rows
        ]

    def save_project(self, project: ProjectPreset) -> None:
        with self._connect() as connection:
            is_enabled = bool(project.is_active)
            if is_enabled:
                connection.execute("UPDATE project_presets SET is_active = 0, fallback_unsorted = 0")

            if project.id is None:
                connection.execute(
                    """
                    INSERT INTO project_presets
                    (name, output_path, naming_pattern, default_tool, is_active, fallback_unsorted)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project.name,
                        project.output_path,
                        project.naming_pattern,
                        project.default_tool,
                        int(is_enabled),
                        int(is_enabled),
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE project_presets
                    SET name = ?, output_path = ?, naming_pattern = ?, default_tool = ?, is_active = ?, fallback_unsorted = ?
                    WHERE id = ?
                    """,
                    (
                        project.name,
                        project.output_path,
                        project.naming_pattern,
                        project.default_tool,
                        int(is_enabled),
                        int(is_enabled),
                        project.id,
                    ),
                )

    def delete_project(self, project_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM project_presets WHERE id = ? AND is_active = 0",
                (project_id,),
            )

    def get_active_project(self) -> ProjectPreset:
        projects = self.list_projects()
        for project in projects:
            if project.is_active:
                return project
        for project in projects:
            if project.fallback_unsorted:
                return project
        raise RuntimeError("No project preset available.")

    def list_rules(self) -> list[DetectionRule]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, tool_name, pattern, priority, is_active
                FROM detection_rules
                ORDER BY priority ASC, tool_name ASC
                """
            ).fetchall()
        return [
            DetectionRule(
                id=row["id"],
                tool_name=row["tool_name"],
                pattern=row["pattern"],
                priority=row["priority"],
                is_active=bool(row["is_active"]),
            )
            for row in rows
        ]

    def save_rule(self, rule: DetectionRule) -> None:
        with self._connect() as connection:
            if rule.id is None:
                connection.execute(
                    """
                    INSERT INTO detection_rules (tool_name, pattern, priority, is_active)
                    VALUES (?, ?, ?, ?)
                    """,
                    (rule.tool_name, rule.pattern, rule.priority, int(rule.is_active)),
                )
            else:
                connection.execute(
                    """
                    UPDATE detection_rules
                    SET tool_name = ?, pattern = ?, priority = ?, is_active = ?
                    WHERE id = ?
                    """,
                    (rule.tool_name, rule.pattern, rule.priority, int(rule.is_active), rule.id),
                )

    def delete_rule(self, rule_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM detection_rules WHERE id = ?", (rule_id,))

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = ?",
                (key,),
            ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def add_log(self, log: RenameLog) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO rename_logs
                (original_name, new_name, source_path, destination_path, detected_tool, project_name, created_at, status, error_message, undone_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.original_name,
                    log.new_name,
                    log.source_path,
                    log.destination_path,
                    log.detected_tool,
                    log.project_name,
                    log.created_at,
                    log.status,
                    log.error_message,
                    log.undone_at,
                ),
            )
            return int(cursor.lastrowid)

    def update_log_status(self, log_id: int, status: str, error_message: str | None = None, undone_at: str | None = None) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE rename_logs
                SET status = ?, error_message = ?, undone_at = COALESCE(?, undone_at)
                WHERE id = ?
                """,
                (status, error_message, undone_at, log_id),
            )

    def list_logs(self, limit: int = 100) -> list[RenameLog]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, original_name, new_name, source_path, destination_path, detected_tool, project_name, created_at, status, error_message, undone_at
                FROM rename_logs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_log(row) for row in rows]

    def list_recent_logs_for_today(self) -> list[RenameLog]:
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, original_name, new_name, source_path, destination_path, detected_tool, project_name, created_at, status, error_message, undone_at
                FROM rename_logs
                WHERE created_at LIKE ?
                ORDER BY created_at DESC
                """,
                (f"{today_prefix}%",),
            ).fetchall()
        return [self._row_to_log(row) for row in rows]

    def get_log(self, log_id: int) -> RenameLog | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, original_name, new_name, source_path, destination_path, detected_tool, project_name, created_at, status, error_message, undone_at
                FROM rename_logs
                WHERE id = ?
                """,
                (log_id,),
            ).fetchone()
        return self._row_to_log(row) if row else None

    def clear_logs(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM rename_logs")

    @staticmethod
    def _row_to_log(row) -> RenameLog:
        return RenameLog(
            id=row["id"],
            original_name=row["original_name"],
            new_name=row["new_name"],
            source_path=row["source_path"],
            destination_path=row["destination_path"],
            detected_tool=row["detected_tool"],
            project_name=row["project_name"],
            created_at=row["created_at"],
            status=row["status"],
            error_message=row["error_message"],
            undone_at=row["undone_at"],
        )



