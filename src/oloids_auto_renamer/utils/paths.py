"""Path helpers for application data and defaults."""

from __future__ import annotations

import os
from pathlib import Path


APP_DIR_NAME = "oloids_auto_renamer"


def get_app_data_dir() -> Path:
    """Return a writable local application data directory."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    app_dir = base / APP_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_database_path() -> Path:
    """Return the SQLite database path."""
    return get_app_data_dir() / "oloids_auto_renamer.db"
