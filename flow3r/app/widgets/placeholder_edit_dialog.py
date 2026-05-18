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
        self._recording_persistence_item_text = "Recording (reset after each recording)"

        # --- Populate all widgets without connecting signals ---
        self.txt_name.setText(self.config.name)

        self.dpd_type.clear()
        for type_key, type_name in PlaceholderConfig.PLACEHOLDER_TYPES.items():
            self.dpd_type.addItem(type_name, type_key)
        idx = self.dpd_type.findData(self.config.type)
        if idx != -1:
            self.dpd_type.setCurrentIndex(idx)

        self.txt_label.setText(self.config.label)

        self.dpd_scope.clear()
        self.dpd_scope.addItem("Global", "global")
        self.dpd_scope.addItem("Group", "group")
        self.dpd_scope.setCurrentIndex(0 if self.config.is_global else 1)

        self.dpd_persistence.clear()
        self.dpd_persistence.addItem("Session (forgotten on restart)", "session")
        self.dpd_persistence.addItem("Project (saved to project file)", "project")
        self.dpd_persistence.addItem(self._recording_persistence_item_text, "recording")
        idx = self.dpd_persistence.findData(self.config.persistence)
        if idx != -1:
            self.dpd_persistence.setCurrentIndex(idx)

        self.chb_constant.setChecked(self.config.is_constant)
        self.txt_value.setText(self.config.constant_value)
        self.txt_description.setText(self.config.description)

        # --- Apply constraints once with correct initial state ---
        self._apply_constraints()

        # --- Connect signals after constraints so init changes don't fire handlers ---
        self.txt_name.editingFinished.connect(self.name_changed)
        self.dpd_type.currentIndexChanged.connect(self.type_changed)
        self.txt_label.editingFinished.connect(self.label_changed)
        self.dpd_scope.currentIndexChanged.connect(self.scope_changed)
        self.dpd_persistence.currentIndexChanged.connect(self.persistence_changed)
        self.chb_constant.stateChanged.connect(self.constant_changed)
        self.txt_value.editingFinished.connect(self.value_changed)
        self.txt_description.textChanged.connect(self.description_changed)

    def name_changed(self):
        self.config.name = self.txt_name.text()

    def type_changed(self):
        self.config.type = self.dpd_type.currentData()

    def label_changed(self):
        self.config.label = self.txt_label.text()

    def scope_changed(self, *_):
        self.config.is_global = self.dpd_scope.currentData() == "global"
        self._apply_constraints()

    def persistence_changed(self, *_):
        self.config.persistence = self.dpd_persistence.currentData()
        self._apply_constraints()

    def _apply_constraints(self):
        is_global = self.dpd_scope.currentData() == "global"
        persistence = self.dpd_persistence.currentData()
        layout = self.frm_placeholder_configuration.layout()

        # "Recording" persistence is only valid for group scope
        recording_idx = self.dpd_persistence.findData("recording")
        if is_global and recording_idx != -1:
            if self.dpd_persistence.currentIndex() == recording_idx:
                self.dpd_persistence.setCurrentIndex(0)
                persistence = self.dpd_persistence.currentData()
                self.config.persistence = persistence
            self.dpd_persistence.removeItem(recording_idx)
        elif not is_global and recording_idx == -1:
            self.dpd_persistence.addItem(self._recording_persistence_item_text, "recording")

        # Constant is only valid for global + project scope
        show_constant = is_global and persistence == "project"
        if not show_constant and self.config.is_constant:
            self.config.is_constant = False
            self.chb_constant.blockSignals(True)
            self.chb_constant.setChecked(False)
            self.chb_constant.blockSignals(False)
        layout.setRowVisible(self.chb_constant, show_constant)
        layout.setRowVisible(self.txt_value, show_constant and self.config.is_constant)

    def constant_changed(self, *_):
        self.config.is_constant = self.chb_constant.isChecked()
        self.frm_placeholder_configuration.layout().setRowVisible(self.txt_value, self.config.is_constant)

    def value_changed(self):
        self.config.constant_value = self.txt_value.text()

    def description_changed(self):
        self.config.description = self.txt_description.toPlainText()
