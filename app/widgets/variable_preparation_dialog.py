from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox

from app.config.welfare_recorder_config import WelfareRecorderConfig
from app.layout.variable_preparation_dialog import Ui_VariablePreparationDialog
from app.controller import Controller


class VariablePreparationDialog(Ui_VariablePreparationDialog, QDialog):
    def __init__(self, controller: Controller, app: WelfareRecorderConfig = None,
                 recordings=None, cameras=None, parent=None):
        super(VariablePreparationDialog, self).__init__(parent)
        self.setupUi(self)

        self.controller = controller

        self.variable_config_list = controller.config.variable_config_list

        self.app = app
        self.recordings = recordings or []
        self.cameras = cameras or []

        self.values_app = list(self.app.variable_values.values()) if self.app else []
        self.missing_values_app = [v.variable_id for v in self.app.variable_values.values() if v.value is None] if self.app else []
        self.changed_values_app = {}

        self.app_title_label = None
        self.widgets_app = {}

        self.chb_hide_filled.stateChanged.connect(self.hide_filled_changed)

        self._build_form()

    def _build_form(self):
        self.app_title_label = QLabel("### Global:")
        self.app_title_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.frm_variables.layout().addRow(self.app_title_label)

        for variable_value in self.values_app:
            variable_config = self.variable_config_list.variables.get(variable_value.variable_id)
            if variable_config.variable_type == "text":
                input_widget = QLineEdit()
                input_widget.setText(variable_config.default_value or "")
                if variable_value.value is not None:
                    input_widget.setText(str(variable_value.value))
                input_widget.textChanged.connect(lambda _, vid=variable_value.variable_id: self.value_changed_text(vid))
            elif variable_config.variable_type == "int":
                input_widget = QSpinBox()
                input_widget.setValue(variable_config.default_value or 0)
                if variable_value.value is not None:
                    input_widget.setValue(int(variable_value.value))
                input_widget.valueChanged.connect(lambda _, vid=variable_value.variable_id: self.value_changed_int(vid))
            elif variable_config.variable_type == "decimal":
                input_widget = QDoubleSpinBox()
                input_widget.setSingleStep(0.1)
                input_widget.setValue(variable_config.default_value or 0.0)
                if variable_value.value is not None:
                    input_widget.setValue(float(variable_value.value))
                input_widget.valueChanged.connect(lambda _, vid=variable_value.variable_id: self.value_changed_decimal(vid))
            else:
                continue
            self.frm_variables.layout().addRow(f"{variable_config.variable_label}:", input_widget)
            self.widgets_app[variable_value.variable_id] = input_widget

        self._hide_filled(True)

    def _hide_filled(self, hide: bool):
        show_app_title = not (hide and len(self.missing_values_app) == 0) and not (len(self.values_app) == 0)
        self.frm_variables.layout().setRowVisible(self.app_title_label, show_app_title)

        for variable_value in [v for v in self.values_app if v.variable_id not in self.missing_values_app]:
            widget = self.widgets_app.get(variable_value.variable_id)
            if widget:
                self.frm_variables.layout().setRowVisible(widget, not hide)

    def hide_filled_changed(self):
        hide = self.chb_hide_filled.isChecked()
        self._hide_filled(hide)

    def value_changed_text(self, variable_id: str):
        widget = self.widgets_app.get(variable_id)
        if widget and isinstance(widget, QLineEdit):
            self.changed_values_app[variable_id] = widget.text()

    def value_changed_int(self, variable_id: str):
        widget = self.widgets_app.get(variable_id)
        if widget and isinstance(widget, QSpinBox):
            self.changed_values_app[variable_id] = widget.value()

    def value_changed_decimal(self, variable_id: str):
        widget = self.widgets_app.get(variable_id)
        if widget and isinstance(widget, QDoubleSpinBox):
            self.changed_values_app[variable_id] = widget.value()

    def accept(self):
        if self.changed_values_app:
            self.controller.set_variables_app.future(self.changed_values_app)
        super().accept()
