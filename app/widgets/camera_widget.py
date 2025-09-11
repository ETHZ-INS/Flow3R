from typing import TYPE_CHECKING

import cv2
import numpy as np
from PySide6 import QtCore
from PySide6.QtCore import Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDockWidget, QMenu, QLabel

from app.layout.camera_widget import Ui_CameraWidget
from app.thread_bound_callable import thread_bound
from app.widgets.recording_controls_widget import RecordingControlsWidget

if TYPE_CHECKING:
    from app.controller import Controller
    from app.widgets.main_window import WelfareRecorder


class CameraWidgetFactory:
    def __init__(self, controller: "Controller", ui: "WelfareRecorder"):
        self.controller = controller
        self.ui = ui

    def create_widget(self, config) -> "CameraWidget":
        camera_id = config["camera_id"]
        camera_name = config["camera_name"]
        recording_id = config.get("recording_id", None)
        recording_name = config.get("recording_name", None)

        widget = CameraWidget(camera_id, camera_name, recording_id, recording_name)

        widget.recording_controls.recording_start.connect(lambda rid: self.controller.start_recording.future(rid))
        widget.recording_controls.recording_stop.connect(lambda rid: self.controller.stop_recording.future(rid))
        widget.recording_controls.fill_variables.connect(lambda rid: self.ui.fill_variables_recording(recording_id=rid))
        widget.retry.connect(lambda cid: self.controller.setup_camera.future(cid))

        widget.edit_camera.connect(self.ui.edit_camera)
        widget.edit_recording.connect(self.ui.edit_camera_group)

        self.controller.group_view_changed.connect(widget.recording_controls.recording_view_changed)
        self.controller.recording_state_changed.connect(widget.recording_controls.recording_state_changed)

        self.controller.check_recording_state.future(recording_id if recording_id is not None else camera_id)

        return widget

    def update_widget(self, widget: "CameraWidget", config) -> "CameraWidget":
        camera_id = config["camera_id"]
        camera_name = config["camera_name"]
        recording_id = config.get("recording_id", None)
        recording_name = config.get("recording_name", None)

        widget.set_camera_config(camera_id, recording_id, camera_name, recording_name)
        return widget


class CameraWidget(Ui_CameraWidget, QDockWidget):
    image_signal = Signal()
    time_signal = Signal()
    status_signal = Signal()

    edit_camera = Signal(str)  # Signal to edit camera configuration
    edit_recording = Signal(str)  # Signal to edit recording configuration
    edit_pipeline = Signal(str)
    retry = Signal(str)  # Signal to retry the camera setup

    def __init__(self, camera_id: str, camera_name: str, recording_id: str = None, recording_name: str = None):
        super(CameraWidget, self).__init__()

        self.setupUi(self)

        self.camera_id = camera_id
        self.recording_id = recording_id or camera_id
        self.camera_name = camera_name
        self.recording_name = recording_name

        print(self.recording_id)

        self.recording_controls = RecordingControlsWidget(self.recording_id, self.recording_name, show_recording_name=False, show_context_menu=False)
        #self.recording_controls_frame = self.recording_controls.frm_controls
        self.frm_content.layout().addWidget(self.recording_controls)

        self.context_menu = QMenu(self)
        self.action_configure_camera = self.context_menu.addAction("Configure Camera")
        self.action_configure_recording = self.context_menu.addAction("Configure Recording")
        self.action_configure_camera.triggered.connect(self.configure_camera)
        self.action_configure_recording.triggered.connect(self.configure_recording)

        self.label.linkActivated.connect(self.on_link_activated)

        self.label.setMinimumSize(20, 20)

        self.image_signal.connect(self.display_image)

        self.current_image = None
        self.current_time = 0.0
        self.camera_message = None
        self.status_type = "neutral"
        self.status_message = None

        self.recording_running = False

        self.set_show_controls(False)

        self._update()

    @thread_bound()
    def set_show_controls(self, show: bool):
        print(f"[CameraWidget] set_show_controls: {show}")
        """Enable or disable the controls in the widget."""
        self.recording_controls.setVisible(show)

    def _update(self):
        title = f"{self.camera_name}"
        if self.recording_name:
            title += f" ({self.recording_name})"
        self.setWindowTitle(title)

    def set_camera_config(self, camera_id: str, recording_id: str, camera_name: str, recording_name: str = None):
        self.camera_id = camera_id
        self.recording_id = recording_id or camera_id
        self.camera_name = camera_name
        self.recording_name = recording_name

        self.recording_controls.set_recording_id(self.recording_id, self.recording_name)
        self._update()

    def set_image(self, image: np.ndarray):
        """Set the current image to be displayed."""
        self.current_image = image
        self.image_signal.emit()

    def set_camera_message(self, message: str, show_retry: bool = False, show_edit: bool = False):
        """Set an error message to be displayed."""
        if show_edit:
            message += "<br><a href=\"edit\">Edit Camera</a>"
        if show_retry:
            message += "<br><a href=\"retry\">Retry</a>"
        self.camera_message = message
        self.image_signal.emit()

    def configure_camera(self):
        self.edit_camera.emit(self.camera_id)

    def configure_recording(self):
        self.edit_recording.emit(self.recording_id)

    def on_link_activated(self, link: str):
        """Handle link activation in the camera message."""
        if link == "retry":
            self.retry_camera_setup()
        elif link == "edit":
            self.edit_camera.emit(self.camera_id)

    def retry_camera_setup(self):
        """Signal to retry the camera setup."""
        print(f"[CameraWidget] retry_camera_setup: {self.camera_id}")
        if self.camera_id is not None:
            print(f"[CameraWidget] emitting retry signal for {self.camera_id}")
            self.set_camera_message("Retrying camera setup...")
            self.retry.emit(self.camera_id)

    def display_image(self):
        if self.camera_message is not None:
            self.label.clear()
            self.label.setText(self.camera_message)
            return

        if self.current_image is None:
            self.label.clear()
            self.label.setText("Waiting for image...")
            return

        label_width = self.label.width()
        label_height = self.label.height()

        image_height, image_width = self.current_image.shape[:2]

        scale = min(label_width / image_width, label_height / image_height)
        new_width = int(image_width * scale)
        new_height = int(image_height * scale)
        resized_image = cv2.resize(self.current_image, (new_width, new_height))

        if resized_image.ndim == 2:  # Grayscale image
            h, w = resized_image.shape
            ch = 1
        else:  # Color image
            h, w, ch = resized_image.shape
        bytes_per_line = ch * w

        # Convert BGR to RGB for displaying in QLabel
        if resized_image.ndim == 2 or ch == 1:
            q_image = QImage(resized_image.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        else:
            rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        self.label.setPixmap(QPixmap.fromImage(q_image))

    def resizeEvent(self, event):
        super(CameraWidget, self).resizeEvent(event)
        self.display_image()

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())
