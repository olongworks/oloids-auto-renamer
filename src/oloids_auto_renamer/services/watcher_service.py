"""Folder watcher service powered by watchdog."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from oloids_auto_renamer.services.processing_service import FileProcessingService


class _WatchHandler(FileSystemEventHandler):
    def __init__(self, watcher_service: "WatcherService") -> None:
        self.watcher_service = watcher_service

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        self.watcher_service.handle_path(Path(event.src_path))

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        self.watcher_service.handle_path(Path(event.src_path))

    def on_moved(self, event) -> None:
        if event.is_directory:
            return
        self.watcher_service.handle_path(Path(event.dest_path))


class WatcherService(QObject):
    """Manage filesystem observation and forward results through Qt signals."""

    processing_completed = Signal(object)
    status_changed = Signal(bool, str)

    def __init__(self, processor: FileProcessingService) -> None:
        super().__init__()
        self.processor = processor
        self.observer: Observer | None = None
        self.watched_folder: Path | None = None

    def start(self, folder_path: str) -> tuple[bool, str]:
        path = Path(folder_path).expanduser()
        if not path.exists() or not path.is_dir():
            return False, "Please choose a valid folder."

        self.stop()
        self.watched_folder = path
        self.observer = Observer()
        self.observer.schedule(_WatchHandler(self), str(path), recursive=False)
        self.observer.start()
        self.status_changed.emit(True, str(path))
        return True, f"Watching {path}"

    def stop(self) -> None:
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2)
            self.observer = None
        self.status_changed.emit(False, str(self.watched_folder or ""))

    def handle_path(self, path: Path) -> None:
        thread = threading.Thread(target=self._process_in_background, args=(path,), daemon=True)
        thread.start()

    def _process_in_background(self, path: Path) -> None:
        result = self.processor.process_file(path)
        if result.status not in {"ignored", "busy", "missing", "retry_pending"}:
            self.processing_completed.emit(result)
