from PySide6.QtCore import QTime
from PySide6.QtWidgets import QDialog, QLayout

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.layout.group_edit_dialog import Ui_GroupEditDialog


class GroupEditDialog(Ui_GroupEditDialog, QDialog):
    def __init__(self, config: GroupConfig, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.frm_recording_configuration.setMinimumWidth(400)

        self.recording_form_groups = {
            "manual": [],
            "timed": [self.tme_duration]
        }

        self.config = config

        if self.config.implicit:
            self.txt_recording_name.setReadOnly(True)
            self.txt_recording_name.setStyleSheet("border: none; background: transparent; padding: 0px; margin: 0px;")

        self.dpd_recording_mode.clear()
        for recording_mode, recording_mode_name in GroupConfig.RECORDING_MODES.items():
            self.dpd_recording_mode.addItem(recording_mode_name, recording_mode)

        self.dpd_recording_mode.currentIndexChanged.connect(self.recording_mode_changed)
        self.txt_recording_name.editingFinished.connect(self.group_name_changed)
        self.tme_duration.timeChanged.connect(self.recording_duration_changed)

        self.update_all()

    def _switch_recording_form_group(self):
        recording_mode = self.config.recording_config.recording_mode

        for group_recording_mode, rows in self.recording_form_groups.items():
            if group_recording_mode == recording_mode:
                continue

            for row in rows:
                if self.frm_recording_configuration.layout().isRowVisible(row):
                    self.frm_recording_configuration.layout().setRowVisible(row, False)

        for row in self.recording_form_groups.get(recording_mode, []):
            if not self.frm_recording_configuration.layout().isRowVisible(row):
                self.frm_recording_configuration.layout().setRowVisible(row, True)

    def update_txt_recording_name(self):
        self.txt_recording_name.setText(self.config.name)

    def update_dpd_recording_mode(self):
        self.dpd_recording_mode.setCurrentIndex(self.dpd_recording_mode.findData(self.config.recording_config.recording_mode))

    def update_tme_duration(self):
        self.tme_duration.setTime(QTime.fromMSecsSinceStartOfDay(int(self.config.recording_config.recording_duration * 1000)))

    def update_all(self):
        self._switch_recording_form_group()
        self.update_txt_recording_name()
        self.update_dpd_recording_mode()
        self.update_tme_duration()

    def group_name_changed(self):
        name = self.txt_recording_name.text()
        self.config.name = name

    def recording_mode_changed(self):
        recording_mode = self.dpd_recording_mode.itemData(self.dpd_recording_mode.currentIndex())
        self.config.recording_config.recording_mode = recording_mode
        self._switch_recording_form_group()

    def recording_duration_changed(self):
        duration: QTime = self.tme_duration.time()
        self.config.recording_config.recording_duration = duration.msecsSinceStartOfDay() / 1000.0  # Convert to seconds
