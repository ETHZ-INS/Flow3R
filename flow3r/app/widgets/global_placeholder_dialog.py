from typing import Dict, List, Optional, Literal

from PySide6.QtCore import Qt, QMargins, QSize, Signal
from PySide6.QtGui import QIcon, QFontMetrics
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QFrame, QHBoxLayout, \
    QSizePolicy, QVBoxLayout, QDialogButtonBox, QWidget, QFormLayout, QToolButton, QFileDialog

from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.placeholder_config import PlaceholderConfig
from flow3r.app.controller.controller import Controller


class PathWidget(QWidget):
    path_changed = Signal(str)

    def __init__(self, mode: Literal["folder", "file"], parent=None):
        super().__init__(parent)
        self.mode = mode

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.layout.setSpacing(0)

        self.txt_path = QLineEdit(self)
        self.txt_path.setMinimumSize(QSize(200, 0))
        self.txt_path.editingFinished.connect(self._path_changed)
        self.layout.addWidget(self.txt_path)

        self.btn_select_folder = QToolButton(self)
        if mode == "folder":
            self.btn_select_folder.setIcon(QIcon.fromTheme("folder"))
        else:
            self.btn_select_folder.setIcon(QIcon.fromTheme("document-open"))
        self.btn_select_folder.clicked.connect(self._select_folder)
        self.layout.addWidget(self.btn_select_folder)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def get_path(self) -> str:
        return self.txt_path.text()

    def set_path(self, path: str):
        self.txt_path.setText(path)

    def _path_changed(self):
        self.path_changed.emit(self.txt_path.text())

    def _select_folder(self):
        if self.mode == "folder":
            path = QFileDialog.getExistingDirectory(self, "Select Folder")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")

        if path:
            self.txt_path.setText(path)
            self.path_changed.emit(path)


class GlobalPlaceholderDialog(QDialog):
    config_snapshot_requested = Signal()
    global_placeholder_values_updated = Signal(object)

    def __init__(self, controller: Controller, parent=None):
        super(GlobalPlaceholderDialog, self).__init__(parent)

        self.controller = controller

        self.setWindowTitle("Global Placeholders")
        self.resize(QSize(600, 400))

        layout = QVBoxLayout(self)

        self.frm_placeholders = QFrame()
        layout.addWidget(self.frm_placeholders)

        self.frm_placeholders_layout = QFormLayout(self.frm_placeholders)

        self.button_box = QDialogButtonBox(self)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self._form_built = False
        self._widgets: Dict[str, QWidget] = {}
        self._changed_values: Dict[str, Optional[str]] = {}

        self.config_snapshot_requested.connect(self.controller.send_config_snapshot)
        self.global_placeholder_values_updated.connect(self.controller.update_global_placeholder_values)

        self.controller.config_snapshot.connect(self._config_snapshot)

        self.config_snapshot_requested.emit()

    def _config_snapshot(self, config: AppConfig):
        if self._form_built:
            return
        self._form_built = True
        self._build_form(list(config.placeholders.values()), config.global_placeholder_values)
        self.adjustSize()

    def _build_form(self, placeholders: List[PlaceholderConfig] , values: Dict[str, str]):
        constant_placeholders = [placeholder_config for placeholder_config in placeholders if placeholder_config.is_global and placeholder_config.is_constant]
        non_constant_placeholders = [placeholder_config for placeholder_config in placeholders if placeholder_config.is_global and not placeholder_config.is_constant]


        if constant_placeholders:
            self.frm_placeholders_layout.addRow(QLabel("## Constants", textFormat=Qt.TextFormat.MarkdownText))
            for placeholder_config in constant_placeholders:
                self.frm_placeholders_layout.addRow(f"{placeholder_config.label}:", QLabel(str(placeholder_config.constant_value)))
            self.frm_placeholders_layout.addRow("", QWidget())  # Add some spacing

        if non_constant_placeholders:
            self.frm_placeholders_layout.addRow(QLabel("## Placeholders", textFormat=Qt.TextFormat.MarkdownText))
            for placeholder_config in non_constant_placeholders:
                value = values.get(placeholder_config.id)
                widget = self._build_widget(placeholder_config, value)
                self.frm_placeholders_layout.addRow(f"{placeholder_config.label}:", widget)
                self._widgets[placeholder_config.id] = widget

    def _build_widget(self, placeholder_config: PlaceholderConfig, value: Optional[str]) -> QWidget:
        if placeholder_config.type == "text":
            return self._build_text_input(placeholder_config, value)
        elif placeholder_config.type == "folder":
            return self._build_folder_path_input(placeholder_config, value)
        elif placeholder_config.type == "file":
            return self._build_file_path_input(placeholder_config, value)
        else:
            raise ValueError(f"Unsupported placeholder type: {placeholder_config.type}")

    def _build_text_input(self, placeholder_config: PlaceholderConfig, value: Optional[str]):
        widget = QLineEdit()
        if value is not None:
            widget.setText(str(value))
        widget.editingFinished.connect(lambda pid=placeholder_config.id: self.value_changed_text(pid))
        return widget

    def _build_folder_path_input(self, placeholder_config: PlaceholderConfig, value: Optional[str]):
        widget = PathWidget(mode="folder")
        if value is not None:
            widget.set_path(str(value))
        widget.path_changed.connect(lambda path, pid=placeholder_config.id: self.value_changed_path(pid))
        return widget

    def _build_file_path_input(self, placeholder_config: PlaceholderConfig, value: Optional[str]):
        widget = PathWidget(mode="file")
        if value is not None:
            widget.set_path(str(value))
        widget.path_changed.connect(lambda path, pid=placeholder_config.id: self.value_changed_path(pid))
        return widget

    def value_changed_text(self, placeholder_id: str):
        widget = self._widgets.get(placeholder_id)
        assert isinstance(widget, QLineEdit)

        self._changed_values[placeholder_id] = widget.text()

    def value_changed_path(self, placeholder_id: str):
        widget = self._widgets.get(placeholder_id)
        assert isinstance(widget, PathWidget)

        self._changed_values[placeholder_id] = widget.get_path()

    def accept(self):
        self.global_placeholder_values_updated.emit(self._changed_values)
        super().accept()
