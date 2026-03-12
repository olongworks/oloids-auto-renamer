"""High-level application orchestration for UI consumers."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from oloids_auto_renamer.database.repository import AppRepository
from oloids_auto_renamer.models.entities import DetectionRule, ProcessingResult, ProjectPreset
from oloids_auto_renamer.services.naming_service import NamingService
from oloids_auto_renamer.services.processing_service import FileProcessingService
from oloids_auto_renamer.services.watcher_service import WatcherService


class AppService(QObject):
    """Connect the database, file processor, and watcher to the UI."""

    logs_changed = Signal()
    projects_changed = Signal()
    rules_changed = Signal()
    watcher_status_changed = Signal(bool, str)
    processing_result = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.repository = AppRepository()
        self.naming_service = NamingService()
        self.processor = FileProcessingService(self.repository, self.naming_service)
        self.watcher = WatcherService(self.processor)
        self.watcher.processing_completed.connect(self._handle_processing_result)
        self.watcher.status_changed.connect(self.watcher_status_changed.emit)

    def _handle_processing_result(self, result: ProcessingResult) -> None:
        self.processing_result.emit(result)
        self.logs_changed.emit()

    def get_projects(self) -> list[ProjectPreset]:
        return self.repository.list_projects()

    def get_active_project(self) -> ProjectPreset:
        return self.repository.get_active_project()

    def save_project(self, project: ProjectPreset) -> None:
        self.repository.save_project(project)
        self.projects_changed.emit()

    def delete_project(self, project_id: int) -> None:
        self.repository.delete_project(project_id)
        self.projects_changed.emit()

    def get_rules(self) -> list[DetectionRule]:
        return self.repository.list_rules()

    def save_rule(self, rule: DetectionRule) -> None:
        self.repository.save_rule(rule)
        self.rules_changed.emit()

    def delete_rule(self, rule_id: int) -> None:
        self.repository.delete_rule(rule_id)
        self.rules_changed.emit()

    def get_logs(self, limit: int = 100):
        return self.repository.list_logs(limit=limit)

    def get_today_processed_count(self) -> int:
        return len([log for log in self.repository.list_recent_logs_for_today() if log.status == "processed"])

    def get_watched_folder(self) -> str:
        return self.repository.get_setting("watched_folder", "")

    def set_watched_folder(self, folder: str) -> None:
        self.repository.set_setting("watched_folder", folder)

    def get_setting(self, key: str, default: str = "") -> str:
        return self.repository.get_setting(key, default)

    def set_setting(self, key: str, value: str) -> None:
        self.repository.set_setting(key, value)

    def start_watching(self) -> tuple[bool, str]:
        watched_folder = self.get_watched_folder()
        ok, message = self.watcher.start(watched_folder)
        if ok:
            self.logs_changed.emit()
        return ok, message

    def stop_watching(self) -> None:
        self.watcher.stop()

    def process_selected_file(self, file_path: str) -> ProcessingResult:
        result = self.processor.process_file(Path(file_path))
        self._handle_processing_result(result)
        return result

    def undo_log(self, log_id: int) -> tuple[bool, str]:
        outcome = self.processor.undo(log_id)
        self.logs_changed.emit()
        return outcome

    def clear_logs(self) -> None:
        self.repository.clear_logs()
        self.logs_changed.emit()


