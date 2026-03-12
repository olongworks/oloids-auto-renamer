"""Core file processing flow for detection, rename, move, logging, and undo."""

from __future__ import annotations

import shutil
import threading
import time
from datetime import datetime
from pathlib import Path

from oloids_auto_renamer.database.repository import AppRepository
from oloids_auto_renamer.models.entities import ProcessingResult, RenameLog
from oloids_auto_renamer.rules.detector import ToolDetector
from oloids_auto_renamer.services.naming_service import NamingService
from oloids_auto_renamer.utils.files import (
    is_image_file,
    is_supported_media_file,
    is_temporary_file,
    is_video_file,
    wait_for_file_ready,
)



class FileProcessingService:
    """Process media files into project folders with persistent logs."""

    def __init__(self, repository: AppRepository, naming_service: NamingService | None = None) -> None:
        self.repository = repository
        self.naming_service = naming_service or NamingService()
        self._in_progress_paths: set[str] = set()
        self._completed_paths: set[str] = set()
        self._lock = threading.Lock()

    def process_file(self, path: Path) -> ProcessingResult:
        path = path.resolve()
        created_at = datetime.now()
        path_key = str(path)

        if not path.exists():
            return ProcessingResult(False, "missing", path, message="File no longer exists.", created_at=created_at)

        if path.is_dir() or not is_supported_media_file(path) or is_temporary_file(path):
            return ProcessingResult(False, "ignored", path, message="File type is ignored.", created_at=created_at)

        with self._lock:
            if path_key in self._completed_paths:
                return ProcessingResult(False, "duplicate_ignored", path, message="File already processed.", created_at=created_at)
            if path_key in self._in_progress_paths:
                return ProcessingResult(False, "busy", path, message="File is already being processed.", created_at=created_at)
            self._in_progress_paths.add(path_key)

        try:
            if not wait_for_file_ready(path, retries=15, delay_seconds=1.0):
                return ProcessingResult(False, "retry_pending", path, message="File is still downloading or locked.", created_at=created_at)

            project = self.repository.get_active_project()
            detector = ToolDetector(self.repository.list_rules())
            match = detector.detect(path.name)
            tool_name = match.tool_name
            if tool_name == "UNKNOWN" and project.default_tool:
                tool_name = project.default_tool

            destination_dir = self._resolve_destination_dir(path, tool_name, project, created_at)
            asset_type = path.suffix.lstrip(".").lower() or "asset"

            destination_path = self.naming_service.resolve_unique_path(
                destination_dir,
                pattern=project.naming_pattern,
                project=project.name,
                tool=tool_name,
                asset_type=asset_type,
                extension=path.suffix,
                now=created_at,
            )
            moved_path = self._move_with_retries(path, destination_path)
            log = RenameLog(
                id=None,
                original_name=path.name,
                new_name=moved_path.name,
                source_path=str(path),
                destination_path=str(moved_path),
                detected_tool=tool_name,
                project_name=project.name,
                created_at=created_at.isoformat(timespec="seconds"),
                status="processed",
                error_message=None,
                undone_at=None,
            )
            self.repository.add_log(log)
            with self._lock:
                self._completed_paths.add(path_key)
            return ProcessingResult(
                success=True,
                status="processed",
                source_path=path,
                destination_path=moved_path,
                detected_tool=tool_name,
                project_name=project.name,
                original_name=path.name,
                new_name=moved_path.name,
                created_at=created_at,
            )
        except Exception as exc:  # noqa: BLE001
            return self._log_failure(path, "failed", str(exc), project_name=project.name if 'project' in locals() else "UNSORTED", detected_tool=tool_name if 'tool_name' in locals() else "UNKNOWN")
        finally:
            with self._lock:
                self._in_progress_paths.discard(path_key)

    def undo(self, log_id: int) -> tuple[bool, str]:
        log = self.repository.get_log(log_id)
        if log is None:
            return False, "Log entry not found."
        if log.status == "undone":
            return False, "This action was already undone."

        destination_path = Path(log.destination_path)
        source_path = Path(log.source_path)
        source_path.parent.mkdir(parents=True, exist_ok=True)

        if not destination_path.exists():
            self.repository.update_log_status(log_id, "undo_failed", "Processed file no longer exists.")
            return False, "Processed file no longer exists."

        try:
            if source_path.exists():
                source_path = self._resolve_original_restore_path(source_path)
            shutil.move(str(destination_path), str(source_path))
            self.repository.update_log_status(
                log_id,
                "undone",
                None,
                datetime.now().isoformat(timespec="seconds"),
            )
            with self._lock:
                self._completed_paths.discard(str(source_path))
            return True, f"Restored to {source_path}"
        except Exception as exc:  # noqa: BLE001
            self.repository.update_log_status(log_id, "undo_failed", str(exc))
            return False, str(exc)

    def _resolve_destination_dir(self, path: Path, tool_name: str, project, now: datetime) -> Path:
        date_folder = Path(f"[{now.strftime('%m%d')}]")
        project_root = Path(project.output_path)
        if tool_name == "Kling" and is_video_file(path):
            return project_root / "Video" / date_folder
        if tool_name == "Higgsfield" and is_image_file(path):
            return project_root / "Image" / date_folder
        return project_root / "AI_GEN" / tool_name / date_folder

    def _log_failure(
        self,
        path: Path,
        status: str,
        message: str,
        *,
        project_name: str = "UNSORTED",
        detected_tool: str = "UNKNOWN",
    ) -> ProcessingResult:
        created_at = datetime.now()
        self.repository.add_log(
            RenameLog(
                id=None,
                original_name=path.name,
                new_name=path.name,
                source_path=str(path),
                destination_path=str(path),
                detected_tool=detected_tool,
                project_name=project_name,
                created_at=created_at.isoformat(timespec="seconds"),
                status=status,
                error_message=message,
                undone_at=None,
            )
        )
        return ProcessingResult(
            success=False,
            status=status,
            source_path=path,
            destination_path=path,
            detected_tool=detected_tool,
            project_name=project_name,
            original_name=path.name,
            new_name=path.name,
            message=message,
            created_at=created_at,
        )

    def _move_with_retries(self, source: Path, destination: Path, retries: int = 5, delay_seconds: float = 1.0) -> Path:
        last_error: Exception | None = None
        for _ in range(retries):
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
                return destination
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(delay_seconds)
        raise RuntimeError(f"Unable to move file after retries: {last_error}")

    def _resolve_original_restore_path(self, path: Path) -> Path:
        for version in range(1, 100):
            candidate = path.with_stem(f"{path.stem}_restored_{version:02d}")
            if not candidate.exists():
                return candidate
        raise RuntimeError("Unable to restore file without overwriting an existing file.")

