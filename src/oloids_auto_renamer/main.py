"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from oloids_auto_renamer.services.app_service import AppService
from oloids_auto_renamer.ui.main_window import MainWindow


def run() -> int:
    """Start the desktop application."""
    app = QApplication(sys.argv)
    app.setApplicationName("OAR")

    icon_path = Path(__file__).resolve().parents[2] / "assets" / "oar.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    service = AppService()
    window = MainWindow(service)
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
