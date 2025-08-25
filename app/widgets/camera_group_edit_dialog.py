from concurrent.futures import Future
from copy import deepcopy

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QDialog, QMessageBox, QLayout

from app.config.recording_config import RecordingConfig
from app.layout.camera_group_edit_dialog import Ui_CameraGroupEditDialog
from app.controller import Controller
from app.thread_bound_callable import thread_bound


class CameraGroupEditDialog(Ui_CameraGroupEditDialog, QDialog):
    def __init__(self, controller: Controller, camera_group_config: RecordingConfig = None, su_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.frm_recording_configuration.setMinimumWidth(400)

        self.recording_form_groups = {
            "manual": [],
            "timed": [self.tme_duration]
        }

        self.controller = controller
        self.new = camera_group_config is None
        self.camera_group_config_list = deepcopy(self.controller.config.recording_config_list)
        self.camera_group_config = deepcopy(camera_group_config) if camera_group_config else RecordingConfig()
        self.su_mode = su_mode

        self.dpd_recording_mode.clear()
        for recording_mode, recording_mode_name in RecordingConfig.RECORDING_MODES.items():
            self.dpd_recording_mode.addItem(recording_mode_name, recording_mode)

        self.dpd_recording_mode.currentIndexChanged.connect(self.recording_mode_changed)

        self.txt_recording_name.editingFinished.connect(self.recording_name_changed)
        self.tme_duration.timeChanged.connect(self.recording_duration_changed)

        self.update_all()

    def _switch_recording_form_group(self):
        recording_mode = self.camera_group_config.recording_mode

        for group_recording_mode, rows in self.recording_form_groups.items():
            if group_recording_mode == recording_mode:
                continue

            for row in rows:
                if self.frm_recording_configuration.layout().isRowVisible(row):
                    self.frm_recording_configuration.layout().setRowVisible(row, False)

        for row in self.recording_form_groups.get(recording_mode, []):
            if not self.frm_recording_configuration.layout().isRowVisible(row):
                self.frm_recording_configuration.layout().setRowVisible(row, True)

        #self.layout().invalidate()
        #new_height = self.sizeHint().height()
        #self.resize(self.width(), new_height)

    def update_txt_recording_name(self):
        enabled = self.su_mode or not self.camera_group_config.is_locked("recording_name")
        self.txt_recording_name.setEnabled(enabled)
        self.txt_recording_name.setText(self.camera_group_config.recording_name)

    def update_dpd_recording_mode(self):
        enabled = self.su_mode or not self.camera_group_config.is_locked("recording_mode")
        self.dpd_recording_mode.setEnabled(enabled)
        self.dpd_recording_mode.setCurrentIndex(self.dpd_recording_mode.findData(self.camera_group_config.recording_mode))

    def update_tme_duration(self):
        enabled = self.su_mode or not self.camera_group_config.is_locked("recording_duration")
        self.tme_duration.setEnabled(enabled)
        self.tme_duration.setTime(QTime.fromMSecsSinceStartOfDay(int(self.camera_group_config.recording_duration * 1000)))

    def update_all(self):
        self._switch_recording_form_group()
        self.update_txt_recording_name()
        self.update_dpd_recording_mode()
        self.update_tme_duration()

    def recording_name_changed(self):
        old_recording_name = self.camera_group_config.recording_name

        existing_names = [rec.recording_name for rec in self.camera_group_config_list.recordings.values() if rec.recording_id != self.camera_group_config.recording_id]

        attempt = 1
        while True:
            postfix = f" ({attempt})" if attempt > 1 else ""
            recording_name = self.txt_recording_name.text().strip() + postfix
            if recording_name and recording_name not in existing_names:
                break
            attempt += 1

        if recording_name == old_recording_name:
            return

        if recording_name != self.txt_recording_name.text().strip():
            self.txt_recording_name.blockSignals(True)
            self.txt_recording_name.setText(recording_name)
            self.txt_recording_name.blockSignals(False)

        self.camera_group_config.recording_name = recording_name

    def recording_mode_changed(self):
        recording_mode = self.dpd_recording_mode.itemData(self.dpd_recording_mode.currentIndex())
        self.camera_group_config.recording_mode = recording_mode
        self._switch_recording_form_group()

    def recording_duration_changed(self):
        duration: QTime = self.tme_duration.time()
        self.camera_group_config.recording_duration = duration.msecsSinceStartOfDay() / 1000.0  # Convert to seconds

    def accept(self):
        if self.new:
            fut = self.controller.add_recording.future(self.camera_group_config)
        else:
            fut = self.controller.update_recording.future(self.camera_group_config)

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
        super().accept()
