"""Reusable dialogs for editing projects and detection rules."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from oloids_auto_renamer.models.entities import DetectionRule, ProjectPreset


DIALOG_STYLESHEET = """
QDialog {
    background: rgba(0, 0, 0, 0.96);
}
QWidget {
    color: #eef3f9;
    font-family: "Helvetica Neue", "Pretendard Variable", "Pretendard", "Arial", sans-serif;
    font-size: 13px;
}
QLineEdit, QSpinBox {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 11px 12px;
    color: #f1f5fb;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1px solid rgba(220, 230, 242, 0.34);
    background: rgba(255, 255, 255, 0.05);
}
QPushButton {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 16px;
    color: #eef3f9;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover { background: rgba(255, 255, 255, 0.08); }
QPushButton:pressed { background: rgba(255, 255, 255, 0.12); }
QDialogButtonBox QPushButton {
    min-width: 88px;
}
QCheckBox {
    spacing: 8px;
    color: rgba(224, 232, 241, 0.84);
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
}
QCheckBox::indicator:unchecked {
    border: 1px solid rgba(255, 255, 255, 0.18);
    background: rgba(255, 255, 255, 0.06);
}
QCheckBox::indicator:checked {
    border: 1px solid rgba(235, 241, 248, 0.58);
    background: rgba(233, 239, 246, 0.92);
}
"""


class ProjectDialog(QDialog):
    def __init__(self, project: ProjectPreset | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Project Preset")
        self.resize(560, 360)
        self.setStyleSheet(DIALOG_STYLESHEET)

        self.name_edit = QLineEdit(project.name if project else "")
        self.output_path_edit = QLineEdit(project.output_path if project else "")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._choose_output_path)

        output_layout = QHBoxLayout()
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(8)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(browse_button)
        output_widget = QWidget()
        output_widget.setLayout(output_layout)

        self.pattern_edit = QLineEdit(project.naming_pattern if project else "{mmdd}_{project}_{seq}")
        self.default_tool_edit = QLineEdit(project.default_tool if project and project.default_tool else "")
        self.active_checkbox = QCheckBox("Active project")
        self.active_checkbox.setChecked(project.is_active if project else False)
        self.unsorted_checkbox = QCheckBox("Fallback project")
        self.unsorted_checkbox.setChecked(project.fallback_unsorted if project else False)

        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(16)
        form.addRow("Name", self.name_edit)
        form.addRow("Output Path", output_widget)
        form.addRow("Naming Pattern", self.pattern_edit)
        form.addRow("Default Tool", self.default_tool_edit)
        form.addRow("", self.active_checkbox)
        form.addRow("", self.unsorted_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.project_id = project.id if project else None

    def _choose_output_path(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if folder:
            self.output_path_edit.setText(folder)

    def to_project(self) -> ProjectPreset:
        return ProjectPreset(
            id=self.project_id,
            name=self.name_edit.text().strip(),
            output_path=self.output_path_edit.text().strip(),
            naming_pattern=self.pattern_edit.text().strip(),
            default_tool=self.default_tool_edit.text().strip() or None,
            is_active=self.active_checkbox.isChecked(),
            fallback_unsorted=self.unsorted_checkbox.isChecked(),
        )


class RuleDialog(QDialog):
    def __init__(self, rule: DetectionRule | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Detection Rule")
        self.resize(520, 290)
        self.setStyleSheet(DIALOG_STYLESHEET)

        self.tool_name_edit = QLineEdit(rule.tool_name if rule else "")
        self.pattern_edit = QLineEdit(rule.pattern if rule else "")
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 9999)
        self.priority_spin.setValue(rule.priority if rule else 100)
        self.active_checkbox = QCheckBox("Enabled")
        self.active_checkbox.setChecked(rule.is_active if rule else True)

        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(16)
        form.addRow("Tool", self.tool_name_edit)
        form.addRow("Regex Pattern", self.pattern_edit)
        form.addRow("Priority", self.priority_spin)
        form.addRow("", self.active_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.rule_id = rule.id if rule else None

    def to_rule(self) -> DetectionRule:
        return DetectionRule(
            id=self.rule_id,
            tool_name=self.tool_name_edit.text().strip(),
            pattern=self.pattern_edit.text().strip(),
            priority=self.priority_spin.value(),
            is_active=self.active_checkbox.isChecked(),
        )





