"""File-related utility helpers."""

from __future__ import annotations

import time
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mov"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS
TEMP_SUFFIXES = {".crdownload", ".part", ".tmp", ".download"}


def is_supported_media_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def is_temporary_file(path: Path) -> bool:
    suffix_lower = path.suffix.lower()
    name_lower = path.name.lower()
    return suffix_lower in TEMP_SUFFIXES or name_lower.startswith("~") or name_lower.endswith(".tmp")


def wait_for_file_ready(path: Path, retries: int = 8, delay_seconds: float = 1.0) -> bool:
    """Wait until a file has a stable, non-zero size and is readable."""
    previous_size = -1
    stable_count = 0

    for _ in range(retries):
        if not path.exists():
            time.sleep(delay_seconds)
            continue

        try:
            size = path.stat().st_size
            if size <= 0:
                time.sleep(delay_seconds)
                continue

            with path.open("rb"):
                pass

            if size == previous_size:
                stable_count += 1
                if stable_count >= 2:
                    return True
            else:
                stable_count = 0
                previous_size = size
        except OSError:
            pass

        time.sleep(delay_seconds)

    return False
