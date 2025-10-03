from concurrent.futures import Future
from copy import deepcopy

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QDialog, QMessageBox, QLayout

from app.config.group_config import GroupConfig
from app.layout.camera_group_edit_dialog import Ui_CameraGroupEditDialog
from app.controller import Controller
from app.thread_bound_callable import thread_bound


class CameraGroupEditDialog(Ui_CameraGroupEditDialog, QDialog):
    def __init__(self, controller: Controller, group: GroupConfig = None, su_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.frm_recording_configuration.setMinimumWidth(400)

        self.recording_form_groups = {
            "manual": [],
            "timed": [self.tme_duration]
        }

        self.controller = controller
        self.su_mode = su_mode
        self.new = group is None

        self.config = controller.get_config()

        if group:
            self.group = deepcopy(group)
        else:
            default_group = self.config.groups.get("default")
            if default_group is None:
                self.group = GroupConfig()
            else:
                new_group = GroupConfig()
                self.group = deepcopy(default_group)
                self.group.group_id = new_group.group_id
                self.group.recording_name = new_group.recording_name

        self.dpd_recording_mode.clear()
        for recording_mode, recording_mode_name in GroupConfig.RECORDING_MODES.items():
            self.dpd_recording_mode.addItem(recording_mode_name, recording_mode)

        self.dpd_recording_mode.currentIndexChanged.connect(self.recording_mode_changed)

        self.txt_recording_name.editingFinished.connect(self.group_name_changed)
        self.tme_duration.timeChanged.connect(self.recording_duration_changed)

        self.update_all()

    def _switch_recording_form_group(self):
        recording_mode = self.group.recording_mode

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
        self.txt_recording_name.setText(self.group.recording_name)
        enabled = self.su_mode or not self.group.is_locked("recording_name")
        self.txt_recording_name.setEnabled(enabled)

    def update_dpd_recording_mode(self):
        self.dpd_recording_mode.setCurrentIndex(self.dpd_recording_mode.findData(self.group.recording_mode))
        enabled = self.su_mode or not self.group.is_locked("recording_mode")
        self.dpd_recording_mode.setEnabled(enabled)

    def update_tme_duration(self):
        self.tme_duration.setTime(QTime.fromMSecsSinceStartOfDay(int(self.group.recording_duration * 1000)))
        enabled = self.su_mode or not self.group.is_locked("recording_duration")
        self.tme_duration.setEnabled(enabled)

    def update_all(self):
        self._switch_recording_form_group()
        self.update_txt_recording_name()
        self.update_dpd_recording_mode()
        self.update_tme_duration()

    def group_name_changed(self):
        old_name = self.group.recording_name
        existing_names = [g.recording_name for g in self.config.groups.values() if g.group_id != self.group.group_id]

        base_name = self.txt_recording_name.text().strip()
        attempt = 1
        while True:
            postfix = f" ({attempt})" if attempt > 1 else ""
            name = base_name + postfix
            if name and name not in existing_names:
                break
            attempt += 1

        if name == old_name:
            return

        if name != base_name:
            self.txt_recording_name.blockSignals(True)
            self.txt_recording_name.setText(name)
            self.txt_recording_name.blockSignals(False)

        self.group.recording_name = name

    def recording_mode_changed(self):
        recording_mode = self.dpd_recording_mode.itemData(self.dpd_recording_mode.currentIndex())
        self.group.recording_mode = recording_mode
        self._switch_recording_form_group()

    def recording_duration_changed(self):
        duration: QTime = self.tme_duration.time()
        self.group.recording_duration = duration.msecsSinceStartOfDay() / 1000.0  # Convert to seconds

    def accept(self):
        if self.new:
            fut = self.controller.add_group.future(self.group)
        else:
            fut = self.controller.update_group.future(self.group)

        fut.add_done_callback(self._config_change_result.future)

    @thread_bound(timeout_ms=2000)
    def _config_change_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error", f"Error while saving configuration: {fut.exception()}")
            return
        super().accept()
