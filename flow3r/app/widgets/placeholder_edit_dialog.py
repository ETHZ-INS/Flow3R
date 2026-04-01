from PySide6.QtWidgets import QDialog, QLayout

from flow3r.app.config.placeholder_config import PlaceholderConfig
from flow3r.app.layout.placeholder_edit_dialog import Ui_PlaceholderEditDialog


class PlaceholderEditDialog(Ui_PlaceholderEditDialog, QDialog):
    def __init__(self, config: PlaceholderConfig, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.frm_placeholder_configuration.setMinimumWidth(400)

        self.config = config

        self.txt_name.setText(self.config.name)
        self.txt_name.editingFinished.connect(self.name_changed)

        self.dpd_type.clear()
        for recording_mode, recording_mode_name in PlaceholderConfig.PLACEHOLDER_TYPES.items():
            self.dpd_type.addItem(recording_mode_name, recording_mode)
        self.dpd_type.currentIndexChanged.connect(self.type_changed)

        self.txt_label.setText(self.config.label)
        self.txt_label.editingFinished.connect(self.label_changed)

        self.chb_global.setChecked(self.config.is_global)
        self.chb_global.stateChanged.connect(self.global_changed)

        self.chb_constant.setChecked(self.config.is_constant)
        self.chb_constant.stateChanged.connect(self.constant_changed)

        self.txt_value.setText(self.config.constant_value)
        self.txt_value.editingFinished.connect(self.value_changed)
        self.frm_placeholder_configuration.layout().setRowVisible(self.txt_value, self.config.is_constant)

        self.txt_description.setText(self.config.description)
        self.txt_description.textChanged.connect(self.description_changed)

    def name_changed(self):
        name = self.txt_name.text()
        self.config.name = name

    def type_changed(self):
        placeholder_type = self.dpd_type.currentData()
        self.config.type = placeholder_type

    def label_changed(self):
        label = self.txt_label.text()
        self.config.label = label

    def global_changed(self, *_):
        self.config.is_global = self.chb_global.isChecked()

    def constant_changed(self, *_):
        self.config.is_constant = self.chb_constant.isChecked()
        self.frm_placeholder_configuration.layout().setRowVisible(self.txt_value, self.config.is_constant)

    def value_changed(self):
        value = self.txt_value.text()
        self.config.constant_value = value

    def description_changed(self):
        description = self.txt_description.toPlainText()
        self.config.description = description
