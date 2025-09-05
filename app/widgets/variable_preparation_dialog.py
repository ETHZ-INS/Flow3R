from typing import List, Dict

from PySide6.QtCore import Qt, QMargins, QSize
from PySide6.QtGui import QIcon, QFontMetrics
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QStyle, QFrame, QHBoxLayout, \
    QSizePolicy

from app.config.welfare_recorder_config import WelfareRecorderConfig
from app.layout.variable_preparation_dialog import Ui_VariablePreparationDialog
from app.controller import Controller
from app.placeholder_context import PlaceholderContext
from app.placeholder_formatter import PlaceholderFormatter
from app.widgets.variable_text_widget import VariableTextWidget


class VariablePreparationDialog(Ui_VariablePreparationDialog, QDialog):
    def __init__(self, controller: Controller, recording_id: str = None, parent=None):
        super(VariablePreparationDialog, self).__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.config = self.controller.get_config()

        self.required_placeholders = set(self.config.get_required_placeholders(recording_id))

        project_placeholders = [v for v in self.config.variable_config_list.variables.values() if v.scope == "project"]
        group_placeholders = [v for v in self.config.variable_config_list.variables.values() if v.scope == "group"]
        camera_placeholders = [v for v in self.config.variable_config_list.variables.values() if v.scope == "camera"]

        self.old_values = {}

        self.scopes: Dict[str|tuple, dict] = {
            "project": {
                "placeholders": project_placeholders,
                "old_values": {v.variable_id: v.value for v in self.config.variable_values.values() if v.value is not None},
                "changed_values": {},
                "widgets": {},
                "title_widget": None
            },
        }

        if recording_id:
            recording_config = self.config.recording_config_list.recordings.get(recording_id)
            if recording_config:
                self.scopes[("group", recording_config.recording_id)] = {
                    "placeholders": group_placeholders,
                    "old_values": {v.variable_id: v.value for v in recording_config.variable_values.values() if v.value is not None},
                    "changed_values": {},
                    "widgets": {},
                    "title_widget": None
                }
                camera_configs = [c for c in self.config.camera_config_list.cameras.values() if c.activated and c.recording_id == recording_id]
                for camera_config in camera_configs:
                    self.scopes[("camera", camera_config.camera_id)] = {
                        "placeholders": camera_placeholders,
                        "old_values": {v.variable_id: v.value for v in camera_config.variable_values.values() if v.value is not None},
                        "changed_values": {},
                        "widgets": {},
                        "title_widget": None
                    }
            else:
                camera_config = self.config.camera_config_list.cameras.get(recording_id)
                if camera_config:
                    self.scopes[("camera", camera_config.camera_id)] = {
                        "placeholders": group_placeholders + camera_placeholders,
                        "old_values": {v.variable_id: v.value for v in camera_config.variable_values.values() if v.value is not None},
                        "changed_values": {},
                        "widgets": {},
                        "title_widget": None
                    }

        self.chb_hide_filled.stateChanged.connect(self.hide_filled_changed)

        self._build_form()

    def _required_dependencies(self) -> set:
        dependencies = set()
        for scope, scope_data in self.scopes.items():
            for placeholder in scope_data["placeholders"]:
                if placeholder.variable_id in scope_data["changed_values"]:
                    value = scope_data["changed_values"].get(placeholder.variable_id)
                else:
                    value = scope_data["old_values"].get(placeholder.variable_id)
                if placeholder.variable_name in self.required_placeholders and value is not None:
                    var_dependencies = PlaceholderFormatter(value).get_placeholders()
                    dependencies.update(var_dependencies)
        union = self.required_placeholders | dependencies
        return union

    def _build_form(self):
        #first_camera_id = None
        #for scope in self.scopes.keys():
        #    if isinstance(scope, tuple) and scope[0] == "camera":
        #        first_camera_id = scope[1]
        #        break

        for scope, scope_data in self.scopes.items():
            icon = None
            if scope == "project":
                title = "Project"
            else:
                scope_type, scope_id = scope
                if scope_type == "group":
                    icon = QIcon(QIcon.fromTheme(u"folder-open"))
                    group = self.config.recording_config_list.recordings.get(scope_id)
                    title = f"{group.recording_name if group else scope_id}"
                elif scope_type == "camera":
                    icon = QIcon(QIcon.fromTheme(u"camera-photo"))
                    camera = self.config.camera_config_list.cameras.get(scope_id)
                    title = f"{camera.camera_name if camera else scope_id}"
                else:
                    title = str(scope_id)

            title_frame = QFrame()
            title_frame.setFrameStyle(QFrame.Shape.NoFrame)
            title_frame.setContentsMargins(QMargins(0, 0, 0, 0))

            title_layout = QHBoxLayout(title_frame)
            title_layout.setContentsMargins(0, 0, 0, 0)

            title_label = QLabel(f"### {title}:")
            title_label.setTextFormat(Qt.TextFormat.MarkdownText)

            h = QFontMetrics(title_label.font()).height()

            if icon is not None:
                icon_label = QLabel()
                icon_label.setPixmap(icon.pixmap(QSize(h, h)))
                icon_label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))
                title_layout.addWidget(icon_label)
            title_layout.addWidget(title_label)

            self.frm_variables.layout().addRow(title_frame)
            scope_data["title_widget"] = title_frame

            for placeholder in scope_data["placeholders"]:
                value = scope_data["old_values"].get(placeholder.variable_id)
                if placeholder.variable_type in ["text", "file", "folder"]:
                    widget = VariableTextWidget(show_preview=False)
                    widget.set_mode(placeholder.variable_type)
                    widget.set_placeholders(list(self.config.variable_config_list.variables.values()))
                    #widget.set_placeholder_context(self.config.get_placeholder_context(first_camera_id))
                    if value is not None:
                        widget.setText(str(value))
                    if placeholder.example_value:
                        widget.txt_value.setPlaceholderText(str(placeholder.example_value))
                    widget.textChanged.connect(lambda s=scope, vid=placeholder.variable_id: self.value_changed_text(s, vid))
                elif placeholder.variable_type == "int":
                    widget = QSpinBox()
                    if value is not None:
                        widget.setValue(int(value))
                    widget.valueChanged.connect(lambda _, s=scope, vid=placeholder.variable_id: self.value_changed_int(s, vid))
                elif placeholder.variable_type == "decimal":
                    widget = QDoubleSpinBox()
                    widget.setSingleStep(0.1)
                    if value is not None:
                        widget.setValue(float(value))
                    widget.valueChanged.connect(lambda _, s=scope, vid=placeholder.variable_id: self.value_changed_decimal(s, vid))
                else:
                    continue
                self.frm_variables.layout().addRow(f"{placeholder.variable_label}:", widget)
                scope_data["widgets"][placeholder.variable_id] = widget

        self._hide_filled(True)

    def _hide_filled(self, hide: bool):
        for scope, scope_data in self.scopes.items():
            print(scope_data["placeholders"])
            print(scope_data["old_values"])
            missing_values = [v.variable_id for v in scope_data["placeholders"] if v.variable_name in self._required_dependencies() and v.variable_id not in scope_data["old_values"]]
            show_title = not (hide and len(missing_values) == 0) and not (len(scope_data["placeholders"]) == 0)
            self.frm_variables.layout().setRowVisible(scope_data["title_widget"], show_title)

            for variable_id, widget in scope_data["widgets"].items():
                if variable_id in missing_values:
                    continue
                if widget:
                    self.frm_variables.layout().setRowVisible(widget, not hide)

    def hide_filled_changed(self):
        hide = self.chb_hide_filled.isChecked()
        self._hide_filled(hide)

    def value_changed_text(self, scope, variable_id: str):
        scope_data = self.scopes.get(scope)
        widget = scope_data["widgets"].get(variable_id)
        if widget and isinstance(widget, (QLineEdit, VariableTextWidget)):
            scope_data["changed_values"][variable_id] = widget.text()
            self.hide_filled_changed()

    def value_changed_int(self, scope, variable_id: str):
        scope_data = self.scopes.get(scope)
        widget = scope_data["widgets"].get(variable_id)
        if widget and isinstance(widget, QSpinBox):
            scope_data["changed_values"][variable_id] = widget.value()

    def value_changed_decimal(self, scope, variable_id: str):
        scope_data = self.scopes.get(scope)
        widget = scope_data["widgets"].get(variable_id)
        if widget and isinstance(widget, QDoubleSpinBox):
            scope_data["changed_values"][variable_id] = widget.value()

    def accept(self):
        for scope, scope_data in self.scopes.items():
            changed_values = scope_data["changed_values"]
            if not changed_values:
                continue
            if scope == "project":
                self.controller.set_variables_project(changed_values)
            else:
                scope_type, scope_id = scope
                if scope_type == "group":
                    self.controller.set_variables_group(scope_id, changed_values)
                elif scope_type == "camera":
                    self.controller.set_variables_camera(scope_id, changed_values)
        super().accept()
