from concurrent.futures import Future
from copy import deepcopy
from pathlib import Path
from typing import List

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QLayout
from pypylon import pylon

from rx import operators as ops
from rx.subject import Subject

from app.config.camera_config import CameraConfig
from app.layout.camera_edit_dialog import Ui_CameraEditDialog
from app.controller import Controller
from app.recording.camera.camera_builder import CameraBuilder
from app.recording.fps_counter_transform import FPSCounterTransform
from app.thread_bound_callable import thread_bound

from app.widgets.camera_preview_dialog import CameraPreviewDialog


def get_available_pylon_devices() -> List[str]:
    devices = list(pylon.TlFactory.GetInstance().EnumerateDevices())
    return [device.GetSerialNumber() for device in devices]


class CameraEditDialog(Ui_CameraEditDialog, QDialog):
    def __init__(self, controller: Controller, camera_config: CameraConfig = None, su_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.frm_camera_config.setMinimumWidth(400)

        self.camera_form_groups = {
            "pylon": [self.dpd_pylon_device, self.frm_pylon_config_file],
            "webcam": [self.spn_webcam_device],
            "video_file": [self.frm_video_file],
        }

        self.controller = controller
        self.new = camera_config is None
        self.su_mode = su_mode

        self.config = controller.get_config()
        self.camera_config = deepcopy(camera_config) if camera_config else CameraConfig()

        self.dpd_group.clear()
        for group_id, group in self.config.groups.items():
            self.dpd_group.addItem(group.recording_name, group_id)

        self.dpd_pipeline.clear()
        for pipeline_id, pipeline in self.config.pipelines.items():
            self.dpd_pipeline.addItem(pipeline.pipeline_name, pipeline_id)

        self.dpd_camera_type.clear()
        for camera_type, camera_type_name in CameraConfig.CAMERA_TYPES.items():
            self.dpd_camera_type.addItem(camera_type_name, camera_type)
        self.dpd_camera_type.setCurrentIndex(self.dpd_camera_type.findData("pylon"))

        self.dpd_pylon_device.clear()
        available_cameras = get_available_pylon_devices()
        for camera in available_cameras:
            self.dpd_pylon_device.addItem(camera)
        self.dpd_pylon_device.setCurrentIndex(0)

        self.btn_select_video_file.clicked.connect(self.select_video_file)
        self.btn_select_pylon_config_file.clicked.connect(self.select_pylon_config_file)

        self.btn_test_camera.setEnabled(self.new)

        self.txt_camera_name.editingFinished.connect(self.camera_name_changed)
        self.dpd_camera_type.currentIndexChanged.connect(self.camera_type_changed)
        self.dpd_pylon_device.currentIndexChanged.connect(self.pylon_device_changed)
        self.spn_webcam_device.valueChanged.connect(self.webcam_device_changed)
        self.dpd_group.currentIndexChanged.connect(self.group_changed)
        self.dpd_pipeline.currentIndexChanged.connect(self.pipeline_changed)

        self.btn_test_camera.clicked.connect(self.test_camera)

        self.update_all()

    def _switch_camera_form_group(self, camera_type: str):
        for group_camera_type, rows in self.camera_form_groups.items():
            if group_camera_type == camera_type:
                continue

            for row in rows:
                self.frm_camera_config.layout().setRowVisible(row, False)

        for row in self.camera_form_groups.get(camera_type, []):
            self.frm_camera_config.layout().setRowVisible(row, True)

        #self.layout().invalidate()
        #new_height = self.sizeHint().height()
        #self.resize(self.width(), new_height)

    def _validate(self) -> str | None:
        # Check if same device is used in other cameras
        conflict_camera_name = None
        for camera_config in self.controller.config.cameras.values():
            if camera_config.camera_id == self.camera_config.camera_id:
                continue
            if camera_config.device_key == self.camera_config.device_key:
                conflict_camera_name = camera_config.camera_name
                break
        if conflict_camera_name:
            return f"Device '{self.camera_config.device_key}' is already used by camera '{conflict_camera_name}'"
        return None

    def update_txt_camera_name(self):
        self.txt_camera_name.setText(self.camera_config.camera_name)
        enabled = self.su_mode or not self.camera_config.is_locked("camera_name")
        self.txt_camera_name.setEnabled(enabled)

    def update_dpd_group(self):
        self.dpd_group.setCurrentIndex(self.dpd_group.findData(self.camera_config.group_id) if self.camera_config.group_id else 0)
        enabled = self.su_mode or not self.camera_config.is_locked("group_id")
        self.dpd_group.setEnabled(enabled)

    def update_dpd_pipeline(self):
        self.dpd_pipeline.setCurrentIndex(self.dpd_pipeline.findData(self.camera_config.pipeline_id) if self.camera_config.pipeline_id else 0)
        enabled = self.su_mode or not self.camera_config.is_locked("pipeline_id")
        self.dpd_pipeline.setEnabled(enabled)

    def update_dpd_camera_type(self):
        self.dpd_camera_type.setCurrentIndex(self.dpd_camera_type.findData(self.camera_config.camera_type))
        enabled = self.su_mode or not self.camera_config.is_locked("camera_type")
        self.dpd_camera_type.setEnabled(enabled)

    def update_dpd_pylon_device(self):
        if self.camera_config.pylon.device_name:
            self.dpd_pylon_device.setCurrentIndex(self.dpd_pylon_device.findText(self.camera_config.pylon.device_name))
        else:
            self.dpd_pylon_device.setCurrentIndex(-1)
        enabled = self.su_mode or not self.camera_config.pylon.is_locked("device_name")
        self.dpd_pylon_device.setEnabled(enabled)

    def update_spn_webcam_device(self):
        self.spn_webcam_device.setValue(self.camera_config.webcam.device_index)
        enabled = self.su_mode or not self.camera_config.webcam.is_locked("device_index")
        self.spn_webcam_device.setEnabled(enabled)

    def update_lbl_video_file(self):
        if self.camera_config.video_file.video_file_path:
            self.lbl_video_file.setText(self.camera_config.video_file.video_file_path)
        else:
            self.lbl_video_file.setText("No file selected")
        enabled = self.su_mode or not self.camera_config.video_file.is_locked("video_file_path")
        self.btn_select_video_file.setEnabled(enabled)

    def update_lbl_pylon_config_file(self):
        if self.camera_config.pylon.config_file_path:
            self.lbl_pylon_config_file.setText(str(self.camera_config.pylon.config_file_path))
        else:
            self.lbl_pylon_config_file.setText("No config file selected")

    def update_btn_select_pylon_config_file(self):
        print("locked values:", self.camera_config.pylon.locked_values)
        visible = self.su_mode or not self.camera_config.pylon.is_locked("config_file_path")
        self.btn_select_pylon_config_file.setVisible(visible)

    def update_btn_ok(self):
        error = self._validate()
        if error:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            self.lbl_status.setText(f'<span style="color: red;">{error}</span>')
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            self.lbl_status.setText('')

    def update_btn_preview(self):
        error = self._validate()
        enabled = self.new and not error
        self.btn_test_camera.setEnabled(enabled)

    def update_all(self):
        self._switch_camera_form_group(self.camera_config.camera_type)

        self.update_txt_camera_name()
        self.update_dpd_group()
        self.update_dpd_pipeline()
        self.update_dpd_camera_type()
        self.update_dpd_pylon_device()
        self.update_spn_webcam_device()
        self.update_lbl_video_file()
        self.update_lbl_pylon_config_file()
        self.update_btn_select_pylon_config_file()
        self.update_btn_ok()
        self.update_btn_preview()

    def camera_name_changed(self):
        old_camera_name = self.camera_config.camera_name
        camera_name = self.txt_camera_name.text().strip()

        camera_names_in_use = [c.camera_name for c in self.controller.config.cameras.values()
                               if c.camera_id != self.camera_config.camera_id]

        if not camera_name or camera_name in camera_names_in_use:
            self.txt_camera_name.setText(old_camera_name)
            return

        self.camera_config.camera_name = camera_name

    def group_changed(self):
        group_id = self.dpd_group.currentData()
        if group_id is not None and not group_id == "default":
            self.camera_config.group_id = group_id
        else:
            self.camera_config.group_id = None

    def pipeline_changed(self):
        pipeline_id = self.dpd_pipeline.currentData()
        if pipeline_id is not None and not pipeline_id == "default":
            self.camera_config.pipeline_id = pipeline_id
        else:
            self.camera_config.pipeline_id = None

    def camera_type_changed(self):
        camera_type = self.dpd_camera_type.currentData()
        self.camera_config.camera_type = camera_type
        self._switch_camera_form_group(camera_type)

    def select_video_file(self):
        from PySide6.QtWidgets import QFileDialog

        video_file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if video_file:
            self.camera_config.video_file.video_file_path = video_file
            self.update_lbl_video_file()

    def select_pylon_config_file(self):
        from PySide6.QtWidgets import QFileDialog

        config_file, _ = QFileDialog.getOpenFileName(self, "Select Pylon Config File", "", "Pylon Config Files (*.pfs)")
        if config_file:
            self.camera_config.pylon.config_file_path = config_file
            self.update_lbl_pylon_config_file()

    def pylon_device_changed(self):
        device_name = self.dpd_pylon_device.currentText().strip()
        if device_name:
            self.camera_config.pylon.device_name = device_name
        else:
            self.camera_config.pylon.device_name = None

    def webcam_device_changed(self):
        device_index = self.spn_webcam_device.value()
        self.camera_config.webcam.device_index = device_index

    def test_camera(self):
        camera_source = CameraBuilder.build(self.camera_config)

        dialog = CameraPreviewDialog(self)
        dialog.setWindowTitle(self.camera_config.camera_name)

        image_future = Future()
        fps_future = Future()

        stop_signal = Subject()

        frames = camera_source.stream.pipe(
            ops.take_until(stop_signal),
            ops.share()
        )

        frames.subscribe(
            lambda frame: dialog.set_image(frame[2]),
            on_error=lambda e: dialog.set_error(f"Camera Error: {e}"),
            on_completed=lambda: image_future.set_result(None)
        )

        frames.pipe(
            FPSCounterTransform()
        ).subscribe(
            lambda fps: dialog.set_fps(fps),
            on_error=lambda e: print(f"Error in FPS stream: {e}"),
            on_completed=lambda: fps_future.set_result(None)
        )

        dialog.exec_()

        stop_signal.on_next(None)

        image_future.result()
        fps_future.result()

    def accept(self):
        error = self._validate()
        if error:
            self.lbl_status.setText(f'<span style="color: red;">{error}</span>')
            return

        if self.new:
            fut = self.controller.add_camera.future(self.camera_config)
        else:
            fut = self.controller.update_camera.future(self.camera_config)

        fut.add_done_callback(self._config_change_result.future)

    @thread_bound(timeout_ms=2000)
    def _config_change_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error saving configuration", str(fut.exception()))
            return
        super().accept()
