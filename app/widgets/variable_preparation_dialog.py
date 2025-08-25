from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox

from app.layout.variable_preparation_dialog import Ui_VariablePreparationDialog
from app.controller import Controller


class VariablePreparationDialog(Ui_VariablePreparationDialog, QDialog):
    def __init__(self, controller: Controller, app=None, recording=None, cameras=None, parent=None):
        super(VariablePreparationDialog, self).__init__(parent)
        self.setupUi(self)

        self.controller = controller

        self.app = app
        self.recording = recording
        self.cameras = cameras or []

        self._build_form()

    def _build_form(self):
        if self.app:
            title_label = QLabel("### Global:")
            title_label.setTextFormat(Qt.TextFormat.MarkdownText)
            self.frm_variables.layout().addRow(title_label)

            for variable_config in self.app:
                if variable_config.variable_type == "text":
                    input_widget = QLineEdit()
                    input_widget.setText(variable_config.default_value or "")
                elif variable_config.variable_type == "int":
                    input_widget = QSpinBox()
                    input_widget.setValue(variable_config.default_value or 0)
                elif variable_config.variable_type == "decimal":
                    input_widget = QDoubleSpinBox()
                    input_widget.setSingleStep(0.1)
                    input_widget.setValue(variable_config.default_value or 0.0)
                else:
                    continue
                self.frm_variables.layout().addRow(f"{variable_config.variable_name}:", input_widget)
