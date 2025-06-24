import uuid
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

from PySide6.QtWidgets import QDialog

from app.config.camera_config import CameraConfig
from app.config.recording_config import RecordingConfig
from app.layout.camera_configuration_dialog import Ui_CameraConfigurationDialog


CAMERA_TYPES = [
    ("pylon", "Pylon Camera"),
    ("video_file", "Video File")
]


class CameraConfigurationDialog(Ui_CameraConfigurationDialog, QDialog):
    def __init__(self, cameras: Dict[str, CameraConfig], parent=None, selected_camera_id: str = None, recording_configs: Dict[str, RecordingConfig] = None):
        super().__init__(parent)
        self.setupUi(self)

        self.cameras = deepcopy(cameras)
        self.current_camera = None

        if len(self.cameras) == 0:
            self.add_camera()

        self.dpd_camera.clear()
        for camera_id, camera_config in self.cameras.items():
            self.dpd_camera.addItem(camera_config.camera_name, camera_config.camera_id)

        self.dpd_group.clear()
        self.dpd_group.addItem("Individual", None)  # Add empty item for no recording
        for recording_id, recording_config in recording_configs.items():
            self.dpd_group.addItem(recording_config.recording_name, recording_id)

        self.dpd_camera_type.clear()
        for camera_type, camera_type_name in CAMERA_TYPES:
            self.dpd_camera_type.addItem(camera_type_name, camera_type)

        self.btn_add_camera.clicked.connect(self.add_camera)
        self.btn_remove_camera.clicked.connect(self.remove_camera)
        self.btn_select_video_file.clicked.connect(self.select_video_file)

        self.dpd_camera.currentIndexChanged.connect(self.current_camera_changed)
        self.txt_camera_name.editingFinished.connect(self.camera_name_changed)
        self.dpd_camera_type.currentIndexChanged.connect(self.camera_type_changed)
        self.dpd_group.currentIndexChanged.connect(self.recording_changed)

        self.dpd_camera.blockSignals(True)
        if selected_camera_id and selected_camera_id in self.cameras:
            self.dpd_camera.setCurrentIndex(self.dpd_camera.findData(selected_camera_id))
        else:
            self.dpd_camera.setCurrentIndex(0)
        self.dpd_camera.blockSignals(False)
        self.current_camera_changed()

    def update_form(self):
        self.txt_camera_name.setText(self.current_camera.camera_name)
        self.dpd_group.setCurrentIndex(self.dpd_group.findData(self.current_camera.recording_id) if self.current_camera.recording_id else 0)
        self.dpd_camera_type.setCurrentIndex(self.dpd_camera_type.findData(self.current_camera.camera_type))
        self.lbl_video_file.setText(str(self.current_camera.video_file.video_file_path) if self.current_camera.video_file.video_file_path else "No file selected")

        if self.current_camera.camera_type == "pylon":
            self.frm_video_file.setVisible(False)
            self.lbl_frm_video_file.setVisible(False)
            self.dpd_pylon_device.setVisible(True)
            self.lbl_dpd_pylon_device.setVisible(True)
        else:
            self.dpd_pylon_device.setVisible(False)
            self.lbl_dpd_pylon_device.setVisible(False)
            self.frm_video_file.setVisible(True)
            self.lbl_frm_video_file.setVisible(True)

        if len(self.cameras) <= 1:
            self.btn_remove_camera.setEnabled(False)
        else:
            self.btn_remove_camera.setEnabled(True)

        self.layout().invalidate()
        new_height = self.sizeHint().height()
        self.resize(self.width(), new_height)

    def add_camera(self):
        num_cameras = len(self.cameras)
        while True:
            camera_name = f"Camera {num_cameras + 1}"
            if camera_name not in self.cameras:
                break
            num_cameras += 1

        camera_id = uuid.uuid4().hex
        camera_config = CameraConfig(camera_id=camera_id, camera_name=camera_name, recording_id=None, camera_type="pylon")
        self.cameras[camera_id] = camera_config
        self.dpd_camera.addItem(camera_name, camera_id)
        self.dpd_camera.setCurrentIndex(self.dpd_camera.findData(camera_id))

    def remove_camera(self):
        current_camera_id = self.dpd_camera.itemData(self.dpd_camera.currentIndex())
        if current_camera_id not in self.cameras:
            return
        if len(self.cameras) <= 1:
            return
        del self.cameras[current_camera_id]

        self.dpd_camera.removeItem(self.dpd_camera.currentIndex())
        self.dpd_camera.setCurrentIndex(0)
        self.current_camera_changed()

    def current_camera_changed(self):
        current_camera_id = self.dpd_camera.itemData(self.dpd_camera.currentIndex())
        self.current_camera = self.cameras.get(current_camera_id, None)
        self.update_form()

    def camera_name_changed(self):
        old_camera_name = self.current_camera.camera_name
        camera_name = self.txt_camera_name.text().strip()
        if not camera_name or camera_name in self.cameras:
            self.txt_camera_name.setText(old_camera_name)
            return

        self.current_camera.camera_name = camera_name
        self.dpd_camera.setItemText(self.dpd_camera.currentIndex(), camera_name)

    def recording_changed(self):
        recording_id = self.dpd_group.currentData()
        if recording_id is not None:
            self.current_camera.recording_id = recording_id
        else:
            self.current_camera.recording_id = None
        self.update_form()

    def camera_type_changed(self):
        camera_type = self.dpd_camera_type.currentData()
        self.current_camera.camera_type = camera_type
        self.update_form()

    def select_video_file(self):
        from PySide6.QtWidgets import QFileDialog

        video_file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if video_file:
            self.current_camera.video_file.video_file_path = Path(video_file)
            self.update_form()
