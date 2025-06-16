import uuid
from copy import deepcopy
from pathlib import Path
from typing import Dict

from PySide6.QtWidgets import QDialog

from app.config.camera_config import CameraConfig
from app.layout.camera_configuration_dialog import Ui_CameraConfigurationDialog


class CameraConfigurationDialog(Ui_CameraConfigurationDialog, QDialog):
    def __init__(self, cameras: Dict[str, CameraConfig], parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.cameras = deepcopy(cameras)

        if len(self.cameras) == 0:
            camera_id = uuid.uuid4().hex
            camera_config = CameraConfig(camera_id=camera_id, camera_name="Camera 1", camera_type="pylon")
            self.cameras["Camera 1"] = camera_config

        camera_names = list(self.cameras.keys())
        self.dpd_camera.clear()
        for camera_name in camera_names:
            self.dpd_camera.addItem(camera_name)

        self.btn_add_camera.clicked.connect(self.add_camera)
        self.btn_remove_camera.clicked.connect(self.remove_camera)
        self.btn_select_video_file.clicked.connect(self.select_video_file)

        self.txt_camera_name.editingFinished.connect(self.camera_name_changed)
        self.dpd_camera_type.currentIndexChanged.connect(self.camera_type_changed)
        self.dpd_camera.currentIndexChanged.connect(self.current_camera_changed)

        self.dpd_camera.setCurrentText("Camera 1")

        self.current_camera = None
        self.current_camera_changed()

    def update_form(self):
        self.txt_camera_name.setText(self.current_camera.camera_name)
        self.dpd_camera_type.setCurrentText(self.current_camera.camera_type.capitalize())
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
        camera_config = CameraConfig(camera_id=camera_id, camera_name=camera_name, camera_type="pylon")
        self.cameras[camera_name] = camera_config
        self.dpd_camera.addItem(camera_name)
        self.dpd_camera.setCurrentText(camera_name)

    def remove_camera(self):
        camera_name = self.dpd_camera.currentText()
        if camera_name not in self.cameras:
            return
        if len(self.cameras) <= 1:
            return
        del self.cameras[camera_name]
        self.dpd_camera.removeItem(self.dpd_camera.currentIndex())
        self.dpd_camera.setCurrentIndex(0)
        self.current_camera_changed()

    def current_camera_changed(self):
        camera_name = self.dpd_camera.currentText()
        camera_config = self.cameras[camera_name]
        self.current_camera = camera_config
        self.update_form()

    def camera_name_changed(self):
        old_camera_name = self.current_camera.camera_name
        camera_name = self.txt_camera_name.text().strip()
        if not camera_name or camera_name in self.cameras:
            self.txt_camera_name.setText(old_camera_name)
            return

        self.current_camera.camera_name = camera_name
        self.dpd_camera.setItemText(self.dpd_camera.currentIndex(), camera_name)
        del self.cameras[old_camera_name]
        self.cameras[camera_name] = self.current_camera

    def camera_type_changed(self):
        camera_type = self.dpd_camera_type.currentText().lower()
        self.current_camera.camera_type = camera_type
        self.cameras[self.current_camera.camera_name] = self.current_camera
        self.update_form()

    def select_video_file(self):
        from PySide6.QtWidgets import QFileDialog

        video_file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if video_file:
            self.current_camera.video_file.video_file_path = Path(video_file)
            self.update_form()
