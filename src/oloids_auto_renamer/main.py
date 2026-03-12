"""Application entry point."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from oloids_auto_renamer.services.app_service import AppService
from oloids_auto_renamer.ui.main_window import MainWindow


def _apply_windows_taskbar_icon(window: MainWindow, icon_path: Path) -> None:
    if sys.platform != "win32" or not icon_path.exists() or icon_path.suffix.lower() != ".ico":
        return
    try:
        hwnd = int(window.winId())
        image_icon = 1
        lr_loadfromfile = 0x10
        lr_defaultsize = 0x40
        wm_seticon = 0x0080
        icon_small = 0
        icon_big = 1
        hicon = ctypes.windll.user32.LoadImageW(None, str(icon_path), image_icon, 0, 0, lr_loadfromfile | lr_defaultsize)
        if hicon:
            ctypes.windll.user32.SendMessageW(hwnd, wm_seticon, icon_small, hicon)
            ctypes.windll.user32.SendMessageW(hwnd, wm_seticon, icon_big, hicon)
    except Exception:
        pass


def run() -> int:
    """Start the desktop application."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("oloids.oar")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("OAR")

    assets_dir = Path(__file__).resolve().parents[2] / "assets"
    icon_path = assets_dir / "oar.ico"
    if not icon_path.exists():
        icon_path = assets_dir / "oar.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    service = AppService()
    window = MainWindow(service)
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    if icon_path.exists():
        _apply_windows_taskbar_icon(window, icon_path)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
