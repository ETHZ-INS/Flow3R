import uuid
from copy import deepcopy
from typing import Dict

from PySide6.QtWidgets import QDialog

from app.config.recording_config import RecordingConfig
from app.layout.recording_configuration_dialog import Ui_RecordingConfigurationDialog


RECORDING_MODES = {
    "manual": "Manual",
    "timed": "Timed",
}


class RecordingConfigurationDialog(Ui_RecordingConfigurationDialog, QDialog):
    def __init__(self, default_recording: RecordingConfig, recordings: Dict[str, RecordingConfig], parent=None, selected_recording_id: str = None):
        super().__init__(parent)
        self.setupUi(self)

        self.default_recording = deepcopy(default_recording)
        self.recordings = deepcopy(recordings)
        self.current_recording = None

        self.dpd_recording.clear()
        self.dpd_recording.addItem("Default", self.default_recording.recording_id)
        for recording_id, recording_config in self.recordings.items():
            self.dpd_recording.addItem(recording_config.recording_name, recording_config.recording_id)

        self.dpd_recording_mode.clear()
        for recording_mode, recording_mode_name in RECORDING_MODES.items():
            self.dpd_recording_mode.addItem(recording_mode_name, recording_mode)

        self.btn_add_recording.clicked.connect(self.add_recording)
        self.btn_remove_recording.clicked.connect(self.remove_recording)

        self.dpd_recording.currentIndexChanged.connect(self.current_recording_changed)
        self.dpd_recording_mode.currentIndexChanged.connect(self.recording_mode_changed)

        self.txt_recording_name.editingFinished.connect(self.recording_name_changed)

        self.dpd_recording.blockSignals(True)
        if selected_recording_id and selected_recording_id in self.recordings:
            self.dpd_recording.setCurrentIndex(self.dpd_recording.findData(selected_recording_id))
        else:
            self.dpd_recording.setCurrentIndex(0)
        self.dpd_recording.blockSignals(False)
        self.current_recording_changed()

    def update_form(self):
        self.txt_recording_name.setText(self.current_recording.recording_name)
        self.dpd_recording_mode.setCurrentIndex(self.dpd_recording_mode.findData(self.current_recording.recording_mode))

        if self.current_recording.recording_mode == "timed":
            self.lbl_tme_duration.setVisible(True)
            self.tme_duration.setVisible(True)
        else:
            self.lbl_tme_duration.setVisible(False)
            self.tme_duration.setVisible(False)

        if self.current_recording.recording_id == "default":
            self.txt_recording_name.setEnabled(False)
        else:
            self.txt_recording_name.setEnabled(True)

        self.layout().invalidate()
        new_height = self.sizeHint().height()
        self.resize(self.width(), new_height)

    def add_recording(self):
        num_recordings = len(self.recordings)
        while True:
            recording_name = f"Group {num_recordings + 1}"
            if recording_name not in self.recordings:
                break
            num_recordings += 1

        recording_id = uuid.uuid4().hex
        recording_config = RecordingConfig(recording_id=recording_id, recording_name=recording_name)
        self.recordings[recording_id] = recording_config
        self.dpd_recording.addItem(recording_name, recording_id)
        self.dpd_recording.setCurrentIndex(self.dpd_recording.findData(recording_id))

    def remove_recording(self):
        current_recording_id = self.dpd_recording.itemData(self.dpd_recording.currentIndex())
        if current_recording_id not in self.recordings:
            return
        if len(self.recordings) <= 1:
            return
        del self.recordings[current_recording_id]

        self.dpd_recording.removeItem(self.dpd_recording.currentIndex())
        self.dpd_recording.setCurrentIndex(0)
        self.current_recording_changed()

    def current_recording_changed(self):
        current_recording_id = self.dpd_recording.itemData(self.dpd_recording.currentIndex())
        if current_recording_id == "default":
            self.current_recording = self.default_recording
        else:
            self.current_recording = self.recordings.get(current_recording_id, None)
        self.update_form()

    def recording_name_changed(self):
        old_recording_name = self.current_recording.recording_name
        recording_name = self.txt_recording_name.text().strip()
        if not recording_name or recording_name in self.recordings:
            self.txt_recording_name.setText(old_recording_name)
            return

        self.current_recording.recording_name = recording_name
        self.dpd_recording.setItemText(self.dpd_recording.currentIndex(), recording_name)

    def recording_mode_changed(self):
        recording_mode = self.dpd_recording_mode.itemData(self.dpd_recording_mode.currentIndex())
        self.current_recording.recording_mode = recording_mode
        self.update_form()
