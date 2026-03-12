"""Dataclasses used across the application."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class ProjectPreset:
    id: Optional[int]
    name: str
    output_path: str
    naming_pattern: str
    default_tool: Optional[str] = None
    is_active: bool = False
    fallback_unsorted: bool = False


@dataclass(slots=True)
class DetectionRule:
    id: Optional[int]
    tool_name: str
    pattern: str
    priority: int = 100
    is_active: bool = True


@dataclass(slots=True)
class RenameLog:
    id: Optional[int]
    original_name: str
    new_name: str
    source_path: str
    destination_path: str
    detected_tool: str
    project_name: str
    created_at: str
    status: str
    error_message: Optional[str] = None
    undone_at: Optional[str] = None


@dataclass(slots=True)
class ProcessingResult:
    success: bool
    status: str
    source_path: Path
    destination_path: Optional[Path] = None
    detected_tool: str = "UNKNOWN"
    project_name: str = "UNSORTED"
    original_name: str = ""
    new_name: str = ""
    message: str = ""
    created_at: datetime | None = None
