"""Main PySide6 desktop window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QEasingCurve, QPointF, QRectF, QSize, Qt, QTimer, QUrl, QVariantAnimation
from PySide6.QtGui import QColor, QDesktopServices, QFont, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from oloids_auto_renamer.models.entities import DetectionRule, ProjectPreset, RenameLog
from oloids_auto_renamer.services.app_service import AppService
from oloids_auto_renamer.ui.dialogs import ProjectDialog, RuleDialog


APP_STYLESHEET = """
QMainWindow { background: #000000; }
QWidget {
    color: #f4f4f4;
    font-family: "Helvetica Neue", "Pretendard Variable", "Pretendard", "Arial", sans-serif;
    font-size: 12px;
}
QTabWidget::pane {
    border: none;
    background: transparent;
    margin-top: 12px;
}
QTabBar::tab {
    background: transparent;
    color: rgba(255, 255, 255, 0.42);
    padding: 14px 0px 16px 0px;
    margin-right: 28px;
    font-size: 12px;
    font-weight: 700;
}
QTabBar::tab:selected {
    color: #ffffff;
    border-bottom: 2px solid rgba(255, 255, 255, 0.94);
}
QTabBar::tab:hover:!selected { color: rgba(255, 255, 255, 0.72); }
QLineEdit {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.09);
    padding: 12px 14px;
    color: #ffffff;
    selection-background-color: rgba(255, 255, 255, 0.14);
}
QLineEdit:focus {
    border: 1px solid rgba(255, 255, 255, 0.22);
    background: rgba(255, 255, 255, 0.05);
}
QTableWidget {
    background: transparent;
    border: none;
    gridline-color: transparent;
    selection-background-color: rgba(255, 255, 255, 0.08);
    selection-color: #ffffff;
}
QHeaderView::section {
    background: transparent;
    color: rgba(255, 255, 255, 0.44);
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.10);
    padding: 0 6px 14px 6px;
    font-size: 10px;
    font-weight: 700;
}
QTableCornerButton::section { background: transparent; border: none; }
QCheckBox {
    spacing: 8px;
    color: rgba(255, 255, 255, 0.84);
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
}
QCheckBox::indicator:unchecked {
    border: 1px solid rgba(255, 255, 255, 0.18);
    background: rgba(255, 255, 255, 0.02);
}
QCheckBox::indicator:checked {
    border: 1px solid rgba(255, 255, 255, 0.70);
    background: rgba(255, 255, 255, 0.94);
}
QStatusBar {
    background: transparent;
    color: rgba(255, 255, 255, 0.48);
}
QMessageBox {
    background: #050505;
}
"""

SHELL_STYLE = """
QFrame#shell {
    background: rgba(0, 0, 0, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 26px;
}
"""

PANEL_STYLE = """
QFrame[panel='true'] {
    background: rgba(0, 0, 0, 0.56);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 18px;
}
"""

HERO_STYLE = """
QFrame[hero='true'] {
    background: rgba(0, 0, 0, 0.62);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 22px;
}
"""

TITLE_TEXT = "color: #ffffff; font-weight: 700;"
MUTED_TEXT = "color: rgba(255, 255, 255, 0.46);"
VALUE_TEXT = "color: #ffffff; font-weight: 700;"
HERO_TITLE = "color: #ffffff; font-weight: 600;"
HERO_MUTED = "color: rgba(255, 255, 255, 0.62);"

class AnimatedBackdrop(QWidget):
    """Minimal black backdrop with restrained interactive spotlight."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self._pointer = QPointF(0.5, 0.38)
        self._pointer_target = QPointF(0.5, 0.38)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def _tick(self) -> None:
        self._pointer = QPointF(
            self._pointer.x() + (self._pointer_target.x() - self._pointer.x()) * 0.12,
            self._pointer.y() + (self._pointer_target.y() - self._pointer.y()) * 0.12,
        )
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: ANN001
        if self.width() and self.height():
            self._pointer_target = QPointF(
                max(0.0, min(1.0, event.position().x() / self.width())),
                max(0.0, min(1.0, event.position().y() / self.height())),
            )
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: ANN001
        self._pointer_target = QPointF(0.5, 0.38)
        super().leaveEvent(event)

    def set_pointer_from_global(self, global_pos) -> None:  # noqa: ANN001
        if global_pos is None or not self.width() or not self.height():
            return
        local = self.mapFromGlobal(global_pos.toPoint())
        self._pointer_target = QPointF(
            max(0.0, min(1.0, local.x() / max(1, self.width()))),
            max(0.0, min(1.0, local.y() / max(1, self.height()))),
        )

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#000000'))
        painter.setRenderHint(QPainter.Antialiasing)

        center = QPointF(self.width() * self._pointer.x(), self.height() * self._pointer.y())
        spotlight = QRadialGradient(center, max(self.width(), self.height()) * 0.22)
        spotlight.setColorAt(0.0, QColor(255, 255, 255, 18))
        spotlight.setColorAt(0.38, QColor(255, 255, 255, 8))
        spotlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(spotlight)
        painter.drawEllipse(center, max(self.width(), self.height()) * 0.22, max(self.width(), self.height()) * 0.22)

class HeroIconLabel(QLabel):
    def __init__(self, icon_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap(str(icon_path))
        self._hover = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(220)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._set_hover)
        self.setFixedSize(44, 44)
        self.setAttribute(Qt.WA_Hover, True)
        self._render()

    def enterEvent(self, event) -> None:  # noqa: ANN001
        self._animate_to(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: ANN001
        self._animate_to(0.0)
        super().leaveEvent(event)

    def _animate_to(self, target: float) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._hover)
        self._animation.setEndValue(target)
        self._animation.start()

    def _set_hover(self, value: float) -> None:
        self._hover = float(value)
        self._render()

    def _render(self) -> None:
        if self._pixmap.isNull():
            self.clear()
            return
        size = int(34 + (self._hover * 3))
        rendered = self._pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(rendered)
        self.setAlignment(Qt.AlignCenter)
class MiniGlyph(QWidget):
    def __init__(self, glyph: str, size: int = 16, color: str = "#fffaf7", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.glyph = glyph
        self.color = QColor(color)
        self.setFixedSize(size, size)
    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.color, 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        rect = QRectF(1.5, 1.5, self.width() - 3, self.height() - 3)
        cx = rect.center().x()
        cy = rect.center().y()
        if self.glyph == "spark":
            painter.drawLine(QPointF(cx, rect.top()), QPointF(cx, rect.bottom()))
            painter.drawLine(QPointF(rect.left(), cy), QPointF(rect.right(), cy))
            painter.drawLine(QPointF(rect.left() + 3, rect.top() + 3), QPointF(rect.right() - 3, rect.bottom() - 3))
            painter.drawLine(QPointF(rect.right() - 3, rect.top() + 3), QPointF(rect.left() + 3, rect.bottom() - 3))
        elif self.glyph == "flow":
            path = QPainterPath(QPointF(rect.left() + 1, cy + 1))
            path.cubicTo(QPointF(cx - 2, rect.top() + 1), QPointF(cx + 2, rect.bottom() - 1), QPointF(rect.right() - 1, cy - 2))
            painter.drawPath(path)
        else:
            painter.drawEllipse(rect.adjusted(2, 2, -2, -2))


class ActionButton(QPushButton):
    def __init__(self, text: str, *, glyph: str, role: str = "secondary", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.glyph = glyph
        self.role = role
        self._progress = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(240)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.valueChanged.connect(self._set_progress)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def sizeHint(self) -> QSize:
        return QSize(max(super().sizeHint().width() + 32, 138), 46)

    def enterEvent(self, event) -> None:  # noqa: ANN001
        self._animate_to(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: ANN001
        self._animate_to(0.0)
        super().leaveEvent(event)

    def _animate_to(self, target: float) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._progress)
        self._animation.setEndValue(target)
        self._animation.start()

    def _set_progress(self, value: float) -> None:
        self._progress = float(value)
        self.update()
    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        bg, fg, stroke = self._colors()

        painter.setPen(QPen(stroke, 1))
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 13, 13)

        if self.text().strip():
            icon_center = QPointF(rect.left() + 18, rect.center().y())
            self._draw_glyph(painter, icon_center, fg)

            painter.setPen(fg)
            font = painter.font()
            font.setPointSize(12)
            font.setWeight(QFont.DemiBold)
            painter.setFont(font)
            painter.drawText(rect.adjusted(34, 0, -18, 0), Qt.AlignVCenter | Qt.AlignLeft, self.text())
        else:
            self._draw_glyph(painter, rect.center(), fg)

    def _colors(self) -> tuple[QColor, QColor, QColor]:
        if not self.isEnabled():
            return QColor(11, 15, 20, 30), QColor(156, 168, 183, 120), QColor(156, 168, 183, 22)
        if self.role == "primary":
            bg = self._mix(QColor("#e7edf5"), QColor("#ffffff"), self._progress * 0.18)
            return bg, QColor("#0b0f14"), QColor(231, 237, 245, 12)
        if self.role == "ghost":
            return QColor(11, 15, 20, 0), self._mix(QColor("#9ca8b7"), QColor("#e7edf5"), self._progress), QColor(156, 168, 183, 0)
        return self._mix(QColor(11, 15, 20, 18), QColor(11, 15, 20, 42), self._progress), QColor("#edf2f8"), self._mix(QColor(156, 168, 183, 26), QColor(156, 168, 183, 54), self._progress)

    @staticmethod
    def _mix(start: QColor, end: QColor, amount: float) -> QColor:
        return QColor(
            int(start.red() + (end.red() - start.red()) * amount),
            int(start.green() + (end.green() - start.green()) * amount),
            int(start.blue() + (end.blue() - start.blue()) * amount),
            int(start.alpha() + (end.alpha() - start.alpha()) * amount),
        )

    def _draw_glyph(self, painter: QPainter, center: QPointF, color: QColor) -> None:
        painter.save()
        painter.setPen(QPen(color, 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        x = center.x()
        y = center.y()
        if self.glyph == "play":
            path = QPainterPath()
            path.moveTo(x - 4, y - 6)
            path.lineTo(x + 7, y)
            path.lineTo(x - 4, y + 6)
            path.closeSubpath()
            painter.fillPath(path, color)
        elif self.glyph == "pause":
            painter.drawLine(QPointF(x - 4, y - 6), QPointF(x - 4, y + 6))
            painter.drawLine(QPointF(x + 4, y - 6), QPointF(x + 4, y + 6))
        elif self.glyph == "plus":
            painter.drawLine(QPointF(x, y - 6), QPointF(x, y + 6))
            painter.drawLine(QPointF(x - 6, y), QPointF(x + 6, y))
        elif self.glyph == "edit":
            painter.drawLine(QPointF(x - 5, y + 5), QPointF(x + 5, y - 5))
            painter.drawLine(QPointF(x - 6, y + 6), QPointF(x - 2, y + 6))
        elif self.glyph == "delete":
            painter.drawRoundedRect(QRectF(x - 5, y - 4, 10, 10), 2, 2)
            painter.drawLine(QPointF(x - 6, y - 4), QPointF(x + 6, y - 4))
        elif self.glyph == "undo":
            painter.drawArc(QRectF(x - 7, y - 7, 14, 14), 35 * 16, 260 * 16)
            painter.drawLine(QPointF(x - 5, y - 2), QPointF(x - 8, y - 6))
            painter.drawLine(QPointF(x - 5, y - 2), QPointF(x - 9, y + 1))
        elif self.glyph == "folder":
            path = QPainterPath(QPointF(x - 8, y + 5))
            path.lineTo(QPointF(x - 6, y - 4))
            path.lineTo(QPointF(x - 1, y - 4))
            path.lineTo(QPointF(x + 1, y - 7))
            path.lineTo(QPointF(x + 8, y - 7))
            path.lineTo(QPointF(x + 6, y + 5))
            path.closeSubpath()
            painter.drawPath(path)
        elif self.glyph == "save":
            painter.drawRoundedRect(QRectF(x - 6, y - 6, 12, 12), 2, 2)
            painter.drawLine(QPointF(x - 3, y - 6), QPointF(x + 3, y - 6))
            painter.drawLine(QPointF(x - 3, y + 2), QPointF(x + 3, y + 2))
        painter.restore()

class ToggleSwitch(QPushButton):
    def __init__(self, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(38, 20)
        self.setFlat(True)
        self._hover = 0.0
        self._position = 1.0 if checked else 0.0
        self._hover_animation = QVariantAnimation(self)
        self._hover_animation.setDuration(160)
        self._hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._hover_animation.valueChanged.connect(self._set_hover)
        self._toggle_animation = QVariantAnimation(self)
        self._toggle_animation.setDuration(180)
        self._toggle_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._toggle_animation.valueChanged.connect(self._set_position)
        self.toggled.connect(self._animate_toggle)

    def sizeHint(self) -> QSize:
        return QSize(38, 20)

    def enterEvent(self, event) -> None:  # noqa: ANN001
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: ANN001
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def _animate_hover(self, target: float) -> None:
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._hover)
        self._hover_animation.setEndValue(target)
        self._hover_animation.start()

    def _set_hover(self, value: float) -> None:
        self._hover = float(value)
        self.update()

    def _animate_toggle(self, checked: bool) -> None:
        self._toggle_animation.stop()
        self._toggle_animation.setStartValue(self._position)
        self._toggle_animation.setEndValue(1.0 if checked else 0.0)
        self._toggle_animation.start()

    def _set_position(self, value: float) -> None:
        self._position = float(value)
        self.update()
    def set_visual_checked(self, checked: bool) -> None:
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)
        self._animate_toggle(checked)


    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2

        off_track = QColor(255, 255, 255, 16 + int(self._hover * 18))
        on_track = QColor(255, 255, 255, 72 + int(self._hover * 32))
        stroke = QColor(255, 255, 255, 34 + int(self._hover * 40))
        glow = QColor(255, 255, 255, 24 + int((self._hover + self._position) * 34))
        knob = QColor("#f6f7f9") if self._position >= 0.5 else QColor(255, 255, 255, 176)

        painter.setPen(Qt.NoPen)
        if self._position > 0.0:
            painter.setBrush(glow)
            painter.drawRoundedRect(rect.adjusted(-1.2, -1.2, 1.2, 1.2), radius + 1.2, radius + 1.2)

        painter.setPen(QPen(stroke, 1.0))
        painter.setBrush(self._mix(off_track, on_track, self._position))
        painter.drawRoundedRect(rect, radius, radius)

        knob_size = rect.height() - 4
        min_x = rect.left() + 2
        max_x = rect.right() - knob_size - 2
        knob_x = min_x + ((max_x - min_x) * self._position)
        knob_rect = QRectF(knob_x, rect.top() + 2, knob_size, knob_size)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 18 + int(self._hover * 20)))
        painter.drawEllipse(knob_rect.adjusted(-0.8, -0.8, 0.8, 0.8))
        painter.setBrush(knob)
        painter.drawEllipse(knob_rect)

    @staticmethod
    def _mix(start: QColor, end: QColor, amount: float) -> QColor:
        return QColor(
            int(start.red() + (end.red() - start.red()) * amount),
            int(start.green() + (end.green() - start.green()) * amount),
            int(start.blue() + (end.blue() - start.blue()) * amount),
            int(start.alpha() + (end.alpha() - start.alpha()) * amount),
        )

class ActivityPreviewPanel(QFrame):
    IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
    VIDEO_SUFFIXES = {".mp4", ".mov"}

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_path: Path | None = None
        self._current_log: RenameLog | None = None
        self.setStyleSheet(
            "QFrame { background: rgba(8, 11, 16, 0.12); border: 1px solid rgba(156, 168, 183, 0.14); border-radius: 0; }"
        )
        self.setMinimumHeight(260)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        self.preview_surface = QLabel("No preview")
        self.preview_surface.setAlignment(Qt.AlignCenter)
        self.preview_surface.setMinimumSize(320, 200)
        self.preview_surface.setStyleSheet(
            "background: rgba(8, 11, 16, 0.18); border: 1px solid rgba(156, 168, 183, 0.16); color: rgba(156, 168, 183, 0.72);"
        )

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(320, 200)
        self.video_widget.setStyleSheet(
            "background: rgba(8, 11, 16, 0.18); border: 1px solid rgba(156, 168, 183, 0.16);"
        )
        self.video_widget.hide()

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setMuted(True)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setLoops(-1)

        surface_wrap = QWidget()
        surface_layout = QVBoxLayout(surface_wrap)
        surface_layout.setContentsMargins(0, 0, 0, 0)
        surface_layout.setSpacing(0)
        surface_layout.addWidget(self.preview_surface)
        surface_layout.addWidget(self.video_widget)

        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 0, 0, 0)
        info_col.setSpacing(10)

        self.preview_title = QLabel("Preview")
        self.preview_title.setStyleSheet("font-size: 22px; font-weight: 700; color: #edf2f8;")
        self.preview_meta = QLabel("Select a processed item to inspect.")
        self.preview_meta.setWordWrap(True)
        self.preview_meta.setStyleSheet("font-size: 13px; color: rgba(156, 168, 183, 0.76);")
        self.preview_path = QLabel("")
        self.preview_path.setWordWrap(True)
        self.preview_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.preview_path.setStyleSheet("font-size: 12px; color: rgba(231, 237, 245, 0.84);")

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(10)
        self.open_file_button = ActionButton("Open File", glyph="play", role="primary")
        self.open_folder_button = ActionButton("Open Folder", glyph="folder", role="secondary")
        self.open_file_button.clicked.connect(self._open_file)
        self.open_folder_button.clicked.connect(self._open_folder)
        button_row.addWidget(self.open_file_button)
        button_row.addWidget(self.open_folder_button)
        button_row.addStretch()

        info_col.addWidget(self.preview_title)
        info_col.addWidget(self.preview_meta)
        info_col.addWidget(self.preview_path)
        info_col.addStretch()
        info_col.addLayout(button_row)

        layout.addWidget(surface_wrap, 3)
        layout.addLayout(info_col, 2)
        self.clear()

    def clear(self) -> None:
        self.media_player.stop()
        self._current_path = None
        self._current_log = None
        self.preview_title.setText("Preview")
        self.preview_meta.setText("Select a processed item to inspect.")
        self.preview_path.setText("")
        self.video_widget.hide()
        self.preview_surface.show()
        self.preview_surface.setPixmap(QPixmap())
        self.preview_surface.setText("No preview")
        self.open_file_button.setEnabled(False)
        self.open_folder_button.setEnabled(False)

    def set_log(self, log: RenameLog | None) -> None:
        if log is None:
            self.clear()
            return

        path = Path(log.destination_path)
        self._current_log = log
        self._current_path = path
        self.preview_title.setText(log.new_name or log.original_name)
        self.preview_meta.setText(f"{log.detected_tool}  |  {log.project_name}  |  {log.status}")
        self.preview_path.setText(str(path))
        self.open_file_button.setEnabled(path.exists())
        self.open_folder_button.setEnabled(path.exists())

        if not path.exists():
            self.media_player.stop()
            self.video_widget.hide()
            self.preview_surface.show()
            self.preview_surface.setPixmap(QPixmap())
            self.preview_surface.setText("File unavailable")
            return

        suffix = path.suffix.lower()
        if suffix in self.IMAGE_SUFFIXES:
            self.media_player.stop()
            self.video_widget.hide()
            self.preview_surface.show()
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                self.preview_surface.setPixmap(QPixmap())
                self.preview_surface.setText("Preview unavailable")
            else:
                scaled = pixmap.scaled(
                    self.preview_surface.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.preview_surface.setPixmap(scaled)
                self.preview_surface.setText("")
        elif suffix in self.VIDEO_SUFFIXES:
            self.preview_surface.clear()
            self.preview_surface.hide()
            self.video_widget.show()
            self.media_player.setSource(QUrl.fromLocalFile(str(path)))
            self.media_player.play()
        else:
            self.media_player.stop()
            self.video_widget.hide()
            self.preview_surface.show()
            self.preview_surface.setPixmap(QPixmap())
            self.preview_surface.setText("Preview unavailable")

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        if self._current_log and self._current_path and self._current_path.exists() and self._current_path.suffix.lower() in self.IMAGE_SUFFIXES:
            self.set_log(self._current_log)

    def _open_file(self) -> None:
        if self._current_path and self._current_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._current_path)))

    def _open_folder(self) -> None:
        if self._current_path and self._current_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._current_path.parent)))
class StatusPill(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(36)
        self.setMinimumWidth(108)
        self.set_status(False)

    def set_status(self, running: bool) -> None:
        self.setText("Running" if running else "Stopped")
        if running:
            self.setStyleSheet(
                "background: rgba(231, 237, 245, 0.96); color: #0b0f14; border-radius: 18px; font-size: 12px; font-weight: 700; padding: 0 14px;"
            )
        else:
            self.setStyleSheet(
                "background: rgba(11, 15, 20, 0.20); color: rgba(231, 237, 245, 0.76); border: 1px solid rgba(156, 168, 183, 0.18); border-radius: 18px; font-size: 12px; font-weight: 700; padding: 0 14px;"
            )

class SectionHeader(QWidget):
    def __init__(self, title: str, description: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(10)
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(
            "background: rgba(255, 255, 255, 0.92); border-radius: 5px;"
        )
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 22px; {TITLE_TEXT}")
        top.addWidget(dot)
        top.addWidget(title_label)
        top.addStretch()

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 12px; {MUTED_TEXT}")
        layout.addLayout(top)
        layout.addWidget(desc)


class MainWindow(QMainWindow):
    def __init__(self, app_service: AppService) -> None:
        super().__init__()
        self.app_service = app_service
        self.setWindowTitle("OAR")
        self.resize(1380, 900)
        self.setStyleSheet(APP_STYLESHEET)
        self.setStatusBar(QStatusBar(self))
        self._dashboard_logs_cache: list[RenameLog] = []
        self._logs_cache: list[RenameLog] = []

        self.backdrop = AnimatedBackdrop()
        root_layout = QVBoxLayout(self.backdrop)
        root_layout.setContentsMargins(26, 24, 26, 18)
        root_layout.setSpacing(0)

        self.shell = QFrame()
        self.shell.setObjectName("shell")
        self.shell.setStyleSheet(SHELL_STYLE + PANEL_STYLE + HERO_STYLE)

        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(22, 18, 22, 18)
        shell_layout.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        shell_layout.addWidget(self.tabs, 1)
        root_layout.addWidget(self.shell)
        self.setCentralWidget(self.backdrop)

        self.dashboard_tab = QWidget()
        self.projects_tab = QWidget()
        self.rules_tab = QWidget()
        self.logs_tab = QWidget()
        self.settings_tab = QWidget()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.projects_tab, "Projects")
        self.tabs.addTab(self.rules_tab, "Rules")
        self.tabs.addTab(self.logs_tab, "Logs")
        self.tabs.addTab(self.settings_tab, "Settings")

        self._build_dashboard_tab()
        self._build_projects_tab()
        self._build_rules_tab()
        self._build_logs_tab()
        self._build_settings_tab()

        self.app_service.projects_changed.connect(self.refresh_projects)
        self.app_service.rules_changed.connect(self.refresh_rules)
        self.app_service.logs_changed.connect(self.refresh_logs)
        self.app_service.logs_changed.connect(self.refresh_dashboard)
        self.app_service.watcher_status_changed.connect(self._update_watcher_status)
        self.app_service.processing_result.connect(self._notify_processing_result)

        self._enable_backdrop_pointer_tracking()
        self.refresh_all()

    def _enable_backdrop_pointer_tracking(self) -> None:
        for widget in [self, *self.findChildren(QWidget)]:
            widget.setMouseTracking(True)
            widget.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:  # noqa: ANN001
        if event.type() == QEvent.MouseMove and hasattr(self, "backdrop"):
            global_pos_method = getattr(event, "globalPosition", None)
            if callable(global_pos_method):
                self.backdrop.set_pointer_from_global(global_pos_method())
        return super().eventFilter(watched, event)
    def _build_dashboard_tab(self) -> None:
        layout = QVBoxLayout(self.dashboard_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setProperty("hero", True)
        hero.setMinimumHeight(300)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(20)

        hero_left = QVBoxLayout()
        hero_left.setSpacing(14)

        intro_row = QHBoxLayout()
        intro_row.setContentsMargins(0, 0, 0, 0)
        intro_row.setSpacing(8)
        intro_label = QLabel("CREATIVE DOWNLOAD AUTOMATION")
        intro_label.setStyleSheet(f"font-size: 10px; font-weight: 700; letter-spacing: 1.2px; {HERO_MUTED}")
        intro_row.addWidget(intro_label)

        hero_icon_path = Path(__file__).resolve().parents[3] / "assets" / "oar.png"
        hero_icon = HeroIconLabel(hero_icon_path)
        intro_row.addWidget(hero_icon)
        intro_row.addStretch()
        self.header_status_badge = StatusPill()
        intro_row.addWidget(self.header_status_badge)

        subheading_row = QHBoxLayout()
        subheading_row.setContentsMargins(0, 0, 0, 0)
        subheading_row.setSpacing(12)

        subheading = QLabel("Watch, rename, and route files automatically.")
        subheading.setWordWrap(True)
        subheading.setMaximumWidth(360)
        subheading.setStyleSheet(f"font-size: 12px; letter-spacing: 0.2px; {HERO_MUTED}")

        license_label = QLabel("licensed by jaewon oh (oloids)")
        license_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        license_label.setStyleSheet(f"font-size: 12px; letter-spacing: 0.2px; {HERO_MUTED}")

        subheading_row.addWidget(subheading, 1)
        subheading_row.addWidget(license_label, 0, Qt.AlignRight)

        meta = QGridLayout()
        meta.setHorizontalSpacing(24)
        meta.setVerticalSpacing(12)
        self.monitor_status_value = self._create_hero_value("Stopped", 17)
        self.watched_folder_value = self._create_hero_value("-", 14)
        meta.addWidget(self._create_metric_block("Status", self.monitor_status_value, True), 0, 0)
        meta.addWidget(self._create_metric_block("Watched folder", self.watched_folder_value, True), 0, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.start_button = ActionButton("", glyph="play", role="primary")
        self.stop_button = ActionButton("", glyph="pause", role="secondary")
        self.start_button.setFixedSize(44, 44)
        self.stop_button.setFixedSize(44, 44)
        self.start_button.setToolTip("Start monitoring")
        self.stop_button.setToolTip("Stop monitoring")
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self._start_monitoring)
        self.stop_button.clicked.connect(self._stop_monitoring)
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addStretch()

        hero_left.addLayout(intro_row)
        hero_left.addLayout(subheading_row)
        hero_left.addLayout(meta)
        hero_left.addLayout(actions)
        hero_layout.addLayout(hero_left, 1)


        summary_row = QGridLayout()
        summary_row.setHorizontalSpacing(12)
        summary_row.setVerticalSpacing(12)
        summary_row.setColumnStretch(0, 1)
        summary_row.setColumnStretch(1, 1)
        summary_row.setColumnStretch(2, 1)
        self.processed_today_value = self._create_value_label("0", 28)
        self.video_archive_value = self._create_value_label("-", 14)
        self.image_archive_value = self._create_value_label("-", 14)
        summary_row.addWidget(self._create_summary_panel("Today", self.processed_today_value, "Completed since midnight."), 0, 0)
        summary_row.addWidget(self._create_summary_panel("Video", self.video_archive_value, "Daily Kling archive."), 0, 1)
        summary_row.addWidget(self._create_summary_panel("Image", self.image_archive_value, "Daily Higgsfield archive."), 0, 2)

        activity = self._create_section_panel("Recent Activity", "Latest items processed by OAR.")
        self.activity_preview = ActivityPreviewPanel()
        activity.layout().addWidget(self.activity_preview)
        activity.layout().addWidget(self._build_activity_controls())
        self.dashboard_logs_table = self._create_logs_table(compact=True)
        self.dashboard_logs_table.itemSelectionChanged.connect(lambda: self._sync_preview_from_table(self.dashboard_logs_table))
        activity.layout().addWidget(self.dashboard_logs_table)

        layout.addWidget(hero)
        layout.addLayout(summary_row)
        layout.addWidget(activity, 1)

    def _build_projects_tab(self) -> None:
        layout = QVBoxLayout(self.projects_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        section = self._create_section_panel("Projects", "Output destinations and naming patterns.")
        row = QHBoxLayout()
        row.setSpacing(10)
        add_button = ActionButton("Add", glyph="plus", role="primary")
        edit_button = ActionButton("Edit", glyph="edit")
        delete_button = ActionButton("Delete", glyph="delete")
        add_button.clicked.connect(self._add_project)
        edit_button.clicked.connect(self._edit_project)
        delete_button.clicked.connect(self._delete_project)
        row.addWidget(add_button)
        row.addWidget(edit_button)
        row.addWidget(delete_button)
        row.addStretch()

        self.projects_table = QTableWidget(0, 5)
        self.projects_table.setHorizontalHeaderLabels(["ID", "Name", "Output Path", "Pattern", "Enabled"])
        self._style_table(self.projects_table)
        self._configure_projects_table()
        section.layout().addLayout(row)
        section.layout().addWidget(self.projects_table)
        layout.addWidget(section)

    def _build_rules_tab(self) -> None:
        layout = QVBoxLayout(self.rules_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        section = self._create_section_panel("Rules", "Filename patterns used to identify each source tool.")
        row = QHBoxLayout()
        row.setSpacing(10)
        add_button = ActionButton("Add", glyph="plus", role="primary")
        edit_button = ActionButton("Edit", glyph="edit")
        delete_button = ActionButton("Delete", glyph="delete")
        add_button.clicked.connect(self._add_rule)
        edit_button.clicked.connect(self._edit_rule)
        delete_button.clicked.connect(self._delete_rule)
        row.addWidget(add_button)
        row.addWidget(edit_button)
        row.addWidget(delete_button)
        row.addStretch()

        self.rules_table = QTableWidget(0, 5)
        self.rules_table.setHorizontalHeaderLabels(["ID", "Tool", "Pattern", "Priority", "Enabled"])
        self._style_table(self.rules_table)
        self._configure_rules_table()
        section.layout().addLayout(row)
        section.layout().addWidget(self.rules_table)
        layout.addWidget(section)

    def _build_logs_tab(self) -> None:
        layout = QVBoxLayout(self.logs_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        section = self._create_section_panel("Logs", "Undo recent actions and inspect completed routing.")
        row = QHBoxLayout()
        row.setSpacing(10)
        self.undo_button = ActionButton("Undo Selected", glyph="undo", role="primary")
        clear_logs_button = ActionButton("Clear Logs", glyph="delete")
        self.undo_button.clicked.connect(self._undo_selected_log)
        clear_logs_button.clicked.connect(self._clear_logs)
        row.addWidget(self.undo_button)
        row.addWidget(clear_logs_button)
        row.addStretch()
        self.logs_table = self._create_logs_table(compact=False)
        self.logs_table.itemSelectionChanged.connect(lambda: self._sync_preview_from_table(self.logs_table))
        self._configure_logs_table(self.logs_table)
        section.layout().addLayout(row)
        section.layout().addWidget(self.logs_table)
        layout.addWidget(section)

    def _build_settings_tab(self) -> None:
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        section = self._create_section_panel("Settings", "Choose the watched folder and basic launch behavior.")
        form = QFormLayout()
        form.setHorizontalSpacing(22)
        form.setVerticalSpacing(18)

        self.watched_folder_edit = QLineEdit()
        browse_button = ActionButton("Browse", glyph="folder", role="ghost")
        browse_button.clicked.connect(self._choose_watch_folder)

        folder_row = QHBoxLayout()
        folder_row.setContentsMargins(0, 0, 0, 0)
        folder_row.setSpacing(10)
        folder_row.addWidget(self.watched_folder_edit)
        folder_row.addWidget(browse_button)
        folder_widget = QWidget()
        folder_widget.setLayout(folder_row)

        self.startup_behavior_checkbox = QCheckBox("Start monitoring on launch")
        self.notifications_checkbox = QCheckBox("Enable notification placeholder")
        save_button = ActionButton("Save Settings", glyph="save", role="primary")
        save_button.clicked.connect(self._save_settings)

        form.addRow(self._create_form_label("Watched Folder"), folder_widget)
        form.addRow(QLabel(""), self.startup_behavior_checkbox)
        form.addRow(QLabel(""), self.notifications_checkbox)

        section.layout().addLayout(form)
        section.layout().addWidget(save_button, 0, Qt.AlignLeft)
        layout.addWidget(section)
        layout.addStretch()

    def _build_activity_controls(self) -> QWidget:
        strip = QWidget()
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self._create_soft_tag("Kling videos", "flow"))
        layout.addWidget(self._create_soft_tag("Higgsfield images", "spark"))
        layout.addWidget(self._create_soft_tag("Daily folders [MMDD]", "flow"))
        layout.addWidget(self._create_logs_project_filter(compact=True))
        clear_logs_button = ActionButton("Clear Logs", glyph="delete")
        clear_logs_button.clicked.connect(self._clear_logs)
        layout.addWidget(clear_logs_button)
        strip.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addStretch()
        return strip

    def _create_logs_project_filter(self, compact: bool) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel("Project")
        label.setStyleSheet("font-size: 12px; font-weight: 700; color: rgba(156, 168, 183, 0.78);")
        combo = QComboBox()
        combo.setMinimumWidth(150 if compact else 180)
        combo.setStyleSheet(
            "QComboBox { background: rgba(11, 15, 20, 0.38); border: 1px solid rgba(156, 168, 183, 0.16); padding: 8px 12px; color: #edf2f8; }"
            "QComboBox::drop-down { border: none; width: 24px; }"
            "QComboBox QAbstractItemView { background: #0f141b; color: #edf2f8; border: 1px solid rgba(156, 168, 183, 0.18); selection-background-color: rgba(231, 237, 245, 0.10); }"
        )
        combo.currentIndexChanged.connect(self._handle_project_filter_change)

        layout.addWidget(label)
        layout.addWidget(combo)

        if compact:
            self.dashboard_project_filter = combo
        else:
            self.logs_project_filter = combo
        return wrapper
    def _create_soft_tag(self, text: str, glyph: str) -> QWidget:
        tag = QFrame()
        tag.setStyleSheet(
            "QFrame { background: transparent; border: 1px solid rgba(156, 168, 183, 0.16); border-radius: 14px; }"
        )
        layout = QHBoxLayout(tag)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(8)
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; font-weight: 600; color: rgba(231, 237, 245, 0.82);")
        layout.addWidget(MiniGlyph(glyph, 14, "#9ca8b7"))
        layout.addWidget(label)
        return tag

    def _create_section_panel(self, title: str, description: str) -> QFrame:
        panel = QFrame()
        panel.setProperty("panel", True)
        panel.setMinimumHeight(124)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)
        layout.addWidget(SectionHeader(title, description))
        return panel

    def _create_summary_panel(self, title: str, value_widget: QLabel, description: str) -> QFrame:
        panel = QFrame()
        panel.setProperty("panel", True)
        panel.setMinimumHeight(124)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: 700; color: rgba(156, 168, 183, 0.72);")
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"font-size: 12px; {MUTED_TEXT}")
        layout.addWidget(title_label)
        layout.addWidget(value_widget)
        layout.addWidget(desc_label)
        layout.addStretch()
        return panel

    def _create_metric_block(self, title: str, value_widget: QLabel, hero: bool = False) -> QWidget:
        block = QWidget()
        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(title)
        label.setStyleSheet(f"font-size: 11px; font-weight: 700; {(HERO_MUTED if hero else MUTED_TEXT)}")
        layout.addWidget(label)
        layout.addWidget(value_widget)
        return block

    def _create_value_label(self, text: str, size: int) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet(f"font-size: {size}px; {VALUE_TEXT}")
        return label

    def _create_hero_value(self, text: str, size: int) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"font-size: {size}px; color: #edf2f8; font-weight: 600;")
        return label

    def _create_form_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 13px; font-weight: 700; color: rgba(236, 242, 248, 0.84);")
        return label

    def _style_table(self, table: QTableWidget) -> None:
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.setFocusPolicy(Qt.NoFocus)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.ElideMiddle)
        table.setStyleSheet(
            "QTableWidget::item { padding: 12px 8px; border-bottom: 1px solid rgba(156, 168, 183, 0.10); color: #edf2f8; }"
            "QTableWidget::item:selected { background: rgba(231, 237, 245, 0.10); }"
        )
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        table.verticalHeader().setDefaultSectionSize(42)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

    def _configure_projects_table(self) -> None:
        header = self.projects_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

    def _configure_rules_table(self) -> None:
        header = self.rules_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

    def _configure_logs_table(self, table: QTableWidget) -> None:
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        table.setColumnWidth(1, 180)
        table.setColumnWidth(2, 180)

    def _create_logs_table(self, compact: bool) -> QTableWidget:
        table = QTableWidget(0, 8)
        table.setHorizontalHeaderLabels(["ID", "Original", "New", "Tool", "Project", "Status", "Created At", "Destination"])
        self._style_table(table)
        self._configure_logs_table(table)
        if compact:
            table.setMaximumHeight(280)
        return table

    def refresh_all(self) -> None:
        self.refresh_projects()
        self.refresh_rules()
        self.refresh_logs()
        self.refresh_dashboard()
        self.refresh_settings()

    def refresh_dashboard(self) -> None:
        self.watched_folder_value.setText(self.app_service.get_watched_folder() or "-")
        self.processed_today_value.setText(str(self.app_service.get_today_processed_count()))
        video_path, image_path = self._project_archive_paths()
        self.video_archive_value.setText(video_path)
        self.image_archive_value.setText(image_path)
        self._dashboard_logs_cache = self.app_service.get_logs(limit=10)
        self._refresh_project_filter_options()
        self._populate_logs_table(self.dashboard_logs_table, self._filtered_logs(self._dashboard_logs_cache, getattr(self, "dashboard_project_filter", None)))
        if self.dashboard_logs_table.rowCount() > 0 and self.dashboard_logs_table.currentRow() < 0:
            self.dashboard_logs_table.selectRow(0)
        self._sync_preview_from_table(self.dashboard_logs_table)

    def _project_archive_paths(self) -> tuple[str, str]:
        project = self.app_service.get_active_project()
        base = Path(project.output_path)
        return str(base / "Video"), str(base / "Image")

    def refresh_projects(self) -> None:
        projects = self.app_service.get_projects()
        self._project_toggle_widgets = {}
        self.projects_table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            values = [
                str(project.id),
                project.name,
                project.output_path,
                project.naming_pattern,
            ]
            for column, value in enumerate(values):
                self.projects_table.setItem(row, column, QTableWidgetItem(value))
            toggle_widget = self._create_project_toggle(project)
            self.projects_table.setCellWidget(row, 4, toggle_widget)

    def _create_project_toggle(self, project: ProjectPreset) -> QWidget:
        wrapper = QWidget()
        wrapper.setFixedSize(52, 28)
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        toggle = ToggleSwitch(project.is_active)
        toggle.setToolTip("Enable this project")
        self._project_toggle_widgets[project.id] = toggle
        toggle.toggled.connect(lambda enabled, project_id=project.id: self._toggle_project(project_id, enabled))
        layout.addWidget(toggle)
        return wrapper

    def _toggle_project(self, project_id: int | None, enabled: bool) -> None:
        if project_id is None:
            return
        project = next((item for item in self.app_service.get_projects() if item.id == project_id), None)
        if project is None:
            return
        if not enabled and project.is_active:
            QMessageBox.information(self, "Project", "Enable another project first.")
            self.refresh_projects()
            return
        if enabled:
            for other_project in self.app_service.get_projects():
                if other_project.id != project_id and other_project.is_active:
                    other_toggle = self._project_toggle_widgets.get(other_project.id)
                    if other_toggle is not None:
                        other_toggle.set_visual_checked(False)
                    break
        QTimer.singleShot(200, lambda project=project, enabled=enabled: self._persist_project_toggle(project, enabled))

    def _persist_project_toggle(self, project: ProjectPreset, enabled: bool) -> None:
        updated = ProjectPreset(
            id=project.id,
            name=project.name,
            output_path=project.output_path,
            naming_pattern=project.naming_pattern,
            default_tool=project.default_tool,
            is_active=enabled,
            fallback_unsorted=enabled,
        )
        self.app_service.save_project(updated)

    def refresh_rules(self) -> None:
        rules = self.app_service.get_rules()
        self.rules_table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            values = [str(rule.id), rule.tool_name, rule.pattern, str(rule.priority), "On" if rule.is_active else "Off"]
            for column, value in enumerate(values):
                self.rules_table.setItem(row, column, QTableWidgetItem(value))

    def refresh_logs(self) -> None:
        self._logs_cache = self.app_service.get_logs(limit=100)
        self._refresh_project_filter_options()
        self._populate_logs_table(self.logs_table, self._filtered_logs(self._logs_cache, getattr(self, "logs_project_filter", None)))
        if self.logs_table.rowCount() > 0 and self.logs_table.currentRow() < 0:
            self.logs_table.selectRow(0)
        self._sync_preview_from_table(self.logs_table)

    def refresh_settings(self) -> None:
        self.watched_folder_edit.setText(self.app_service.get_watched_folder())
        self.startup_behavior_checkbox.setChecked(self.app_service.get_setting("startup_behavior", "manual") == "auto")
        self.notifications_checkbox.setChecked(self.app_service.get_setting("notifications_enabled", "1") == "1")

    def _populate_logs_table(self, table: QTableWidget, logs: list[RenameLog]) -> None:
        table.setSortingEnabled(False)
        table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            values = [
                str(log.id),
                log.original_name,
                log.new_name,
                log.detected_tool,
                log.project_name,
                log.status,
                log.created_at,
                log.destination_path,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setData(Qt.UserRole, log)
                table.setItem(row, column, item)
        table.setSortingEnabled(True)
        table.sortItems(4, Qt.AscendingOrder)

    def _refresh_project_filter_options(self) -> None:
        project_names = sorted({project.name for project in self.app_service.get_projects()})
        extra_names = sorted({log.project_name for log in [*self._dashboard_logs_cache, *self._logs_cache] if log.project_name})
        for name in extra_names:
            if name not in project_names:
                project_names.append(name)
        values = ["All Projects", *project_names]
        for combo_name in ("dashboard_project_filter", "logs_project_filter"):
            combo = getattr(self, combo_name, None)
            if combo is None:
                continue
            current = combo.currentText() or "All Projects"
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(values)
            index = combo.findText(current)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    def _filtered_logs(self, logs: list[RenameLog], combo: QComboBox | None) -> list[RenameLog]:
        if combo is None:
            return logs
        current = combo.currentText().strip()
        if not current or current == "All Projects":
            return logs
        return [log for log in logs if log.project_name == current]

    def _handle_project_filter_change(self) -> None:
        if hasattr(self, "dashboard_logs_table"):
            self._populate_logs_table(
                self.dashboard_logs_table,
                self._filtered_logs(self._dashboard_logs_cache, getattr(self, "dashboard_project_filter", None)),
            )
            if self.dashboard_logs_table.rowCount() > 0:
                self.dashboard_logs_table.selectRow(0)
            else:
                self.activity_preview.clear()
        if hasattr(self, "logs_table"):
            self._populate_logs_table(
                self.logs_table,
                self._filtered_logs(self._logs_cache, getattr(self, "logs_project_filter", None)),
            )
            if self.logs_table.rowCount() > 0:
                self.logs_table.selectRow(0)
                self._sync_preview_from_table(self.logs_table)

    def _start_monitoring(self) -> None:
        ok, message = self.app_service.start_watching()
        if not ok:
            QMessageBox.warning(self, "Monitoring", message)
        else:
            self.statusBar().showMessage(message, 5000)

    def _stop_monitoring(self) -> None:
        self.app_service.stop_watching()
        self.statusBar().showMessage("Monitoring stopped.", 5000)

    def _update_watcher_status(self, running: bool, folder: str) -> None:
        self.monitor_status_value.setText("Running" if running else "Stopped")
        self.header_status_badge.set_status(running)
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.watched_folder_value.setText(folder or "-")

    def _notify_processing_result(self, result) -> None:
        message = result.new_name if result.success else result.message
        self.statusBar().showMessage(f"{result.status}: {message}", 7000)

    def _clear_logs(self) -> None:
        answer = QMessageBox.question(
            self,
            "Clear Logs",
            "Delete all log history from the app?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.app_service.clear_logs()
        self.statusBar().showMessage("Logs cleared.", 5000)
        if hasattr(self, "activity_preview"):
            self.activity_preview.clear()

    def _selected_log_from_table(self, table: QTableWidget) -> RenameLog | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _sync_preview_from_table(self, table: QTableWidget) -> None:
        if hasattr(self, "activity_preview"):
            self.activity_preview.set_log(self._selected_log_from_table(table))

    def _choose_watch_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose Watched Folder")
        if folder:
            self.watched_folder_edit.setText(folder)

    def _save_settings(self) -> None:
        self.app_service.set_watched_folder(self.watched_folder_edit.text().strip())
        self.app_service.set_setting("startup_behavior", "auto" if self.startup_behavior_checkbox.isChecked() else "manual")
        self.app_service.set_setting("notifications_enabled", "1" if self.notifications_checkbox.isChecked() else "0")
        self.refresh_dashboard()
        QMessageBox.information(self, "Settings", "Settings saved.")

    def _selected_table_id(self, table: QTableWidget) -> int | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        return int(item.text()) if item else None

    def _selected_project(self) -> ProjectPreset | None:
        selected_id = self._selected_table_id(self.projects_table)
        if selected_id is None:
            return None
        for project in self.app_service.get_projects():
            if project.id == selected_id:
                return project
        return None

    def _selected_rule(self) -> DetectionRule | None:
        selected_id = self._selected_table_id(self.rules_table)
        if selected_id is None:
            return None
        for rule in self.app_service.get_rules():
            if rule.id == selected_id:
                return rule
        return None

    def _add_project(self) -> None:
        dialog = ProjectDialog(parent=self)
        if dialog.exec():
            project = dialog.to_project()
            if not project.name or not project.output_path or not project.naming_pattern:
                QMessageBox.warning(self, "Project", "Name, output path, and naming pattern are required.")
                return
            self.app_service.save_project(project)

    def _edit_project(self) -> None:
        project = self._selected_project()
        if project is None:
            QMessageBox.information(self, "Project", "Select a project first.")
            return
        dialog = ProjectDialog(project, self)
        if dialog.exec():
            updated = dialog.to_project()
            if not updated.name or not updated.output_path or not updated.naming_pattern:
                QMessageBox.warning(self, "Project", "Name, output path, and naming pattern are required.")
                return
            self.app_service.save_project(updated)

    def _delete_project(self) -> None:
        project = self._selected_project()
        if project is None:
            QMessageBox.information(self, "Project", "Select a project first.")
            return
        if project.is_active:
            QMessageBox.warning(self, "Project", "Disable this project by enabling another project first.")
            return
        self.app_service.delete_project(project.id)

    def _add_rule(self) -> None:
        dialog = RuleDialog(parent=self)
        if dialog.exec():
            rule = dialog.to_rule()
            if not rule.tool_name or not rule.pattern:
                QMessageBox.warning(self, "Rule", "Tool and regex pattern are required.")
                return
            self.app_service.save_rule(rule)

    def _edit_rule(self) -> None:
        rule = self._selected_rule()
        if rule is None:
            QMessageBox.information(self, "Rule", "Select a rule first.")
            return
        dialog = RuleDialog(rule, self)
        if dialog.exec():
            updated = dialog.to_rule()
            if not updated.tool_name or not updated.pattern:
                QMessageBox.warning(self, "Rule", "Tool and regex pattern are required.")
                return
            self.app_service.save_rule(updated)

    def _delete_rule(self) -> None:
        rule = self._selected_rule()
        if rule is None:
            QMessageBox.information(self, "Rule", "Select a rule first.")
            return
        self.app_service.delete_rule(rule.id)

    def _undo_selected_log(self) -> None:
        selected_id = self._selected_table_id(self.logs_table)
        if selected_id is None:
            QMessageBox.information(self, "Undo", "Select a log entry first.")
            return
        success, message = self.app_service.undo_log(selected_id)
        if success:
            QMessageBox.information(self, "Undo", message)
        else:
            QMessageBox.warning(self, "Undo", message)























































































