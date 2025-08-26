from concurrent.futures import Future
from copy import deepcopy

from PySide6.QtWidgets import QDialog, QMessageBox, QLayout

from app.config.variable_config import VariableConfig
from app.controller import Controller
from app.layout.variable_edit_dialog import Ui_VariableEditDialog
from app.thread_bound_callable import thread_bound


class VariableEditDialog(Ui_VariableEditDialog, QDialog):
    def __init__(self, controller: Controller, variable_config: VariableConfig = None, su_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.frm_configuration.setMinimumWidth(400)

        self.form_groups = {}

        self.controller = controller
        self.new = variable_config is None
        self.variable_config_list = deepcopy(self.controller.config.variable_config_list)
        self.variable_config = deepcopy(variable_config) if variable_config else VariableConfig()
        self.su_mode = su_mode

        self.dpd_variable_type.clear()
        for variable_type, variable_type_name in VariableConfig.VARIABLE_TYPES.items():
            self.dpd_variable_type.addItem(variable_type_name, variable_type)

        self.txt_name.editingFinished.connect(self.name_changed)
        self.txt_label.editingFinished.connect(self.label_changed)
        self.dpd_variable_type.currentIndexChanged.connect(self.variable_type_changed)
        self.txt_description.textChanged.connect(self.description_changed)

        self.update_all()

    def _switch_form_group(self):
        pass

    def update_txt_name(self):
        enabled = self.su_mode or not self.variable_config.is_locked("variable_name")
        self.txt_name.setEnabled(enabled)
        self.txt_name.setText(self.variable_config.variable_name)

    def update_txt_label(self):
        enabled = self.su_mode or not self.variable_config.is_locked("variable_label")
        self.txt_label.setEnabled(enabled)
        self.txt_label.setText(self.variable_config.variable_label)

    def update_dpd_variable_type(self):
        enabled = self.su_mode or not self.variable_config.is_locked("variable_type")
        self.dpd_variable_type.setEnabled(enabled)
        self.dpd_variable_type.setCurrentIndex(self.dpd_variable_type.findData(self.variable_config.variable_type))

    def update_txr_description(self):
        enabled = self.su_mode or not self.variable_config.is_locked("description")
        self.txt_description.setEnabled(enabled)
        self.txt_description.setText(self.variable_config.description)

    def update_all(self):
        self.update_txt_name()
        self.update_txt_label()
        self.update_dpd_variable_type()
        self.update_txr_description()

    def name_changed(self):
        old_name = self.variable_config.variable_name
        new_name = self.txt_name.text().strip()

        if new_name == old_name:
            return

        existing_names = [var.variable_name for var in self.variable_config_list.variables.values()]

        if new_name in existing_names:
            QMessageBox.critical(self, "Error", f"A variable with the name '{new_name}' already exists. Please choose a different name.")
            self.txt_name.blockSignals(True)
            self.txt_name.setText(old_name)
            self.txt_name.blockSignals(False)
            return

        self.variable_config.variable_name = new_name

    def label_changed(self):
        new_label = self.txt_label.text().strip()
        self.variable_config.variable_label = new_label

    def variable_type_changed(self):
        variable_type = self.dpd_variable_type.itemData(self.dpd_variable_type.currentIndex())
        self.variable_config.variable_type = variable_type

    def description_changed(self):
        new_description = self.txt_description.toPlainText()
        self.variable_config.description = new_description

    def accept(self):
        if self.new:
            fut = self.controller.add_variable.future(self.variable_config)
        else:
            fut = self.controller.update_variable.future(self.variable_config)

        fut.add_done_callback(self._config_change_result.future)

    @thread_bound(timeout_ms=2000)
    def _config_change_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error", f"Error while saving configuration: {fut.exception()}")
            return
        else:
            res = fut.result()
            if not res.success:
                QMessageBox.critical(self, "Error", f"Error while saving configuration: {res.message}")
                return
        self.controller.attach_variable_to_app(self.variable_config.variable_id)
        super().accept()
