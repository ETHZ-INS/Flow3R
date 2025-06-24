from typing import Dict, Tuple
import time

import cv2
import numpy as np
from PySide6 import QtCore
from PySide6.QtCore import Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDockWidget, QMenu

import rx
from rx import operators as ops
from rx.scheduler import ThreadPoolScheduler

from app.config.camera_config import CameraConfig
from app.config.recording_config import RecordingConfig
from app.layout.camera_widget import Ui_CameraWidget


class CameraWidget(Ui_CameraWidget, QDockWidget):
    image_signal = Signal()
    configure_camera_signal = Signal(str)
    configure_recording_signal = Signal(str)
    start_signal = Signal()

    def __init__(self):
        super(CameraWidget, self).__init__()

        self.setupUi(self)

        self.context_menu = QMenu(self)
        self.action_configure_camera = self.context_menu.addAction("Configure Camera")
        self.action_configure_recording = self.context_menu.addAction("Configure Recording")
        self.action_configure_camera.triggered.connect(self.on_configure_camera)
        self.action_configure_recording.triggered.connect(self.on_configure_recording)

        self._worker = ThreadPoolScheduler(1)
        self._sub = None

        self.label.setMinimumSize(20, 20)

        self.image_signal.connect(self.display_image)

        self.current_image = None
        self.current_time = 0.0

    def set_camera_config(self, camera_config: CameraConfig, recording_name: str = None):
        self.camera_id = camera_config.camera_id
        self.recording_id = camera_config.recording_id

        title = f"{camera_config.camera_name}"
        if recording_name:
            title += f" ({recording_name})"
        self.setWindowTitle(title)

    def on_configure_camera(self):
        self.configure_camera_signal.emit(self.camera_id)

    def on_configure_recording(self):
        self.configure_recording_signal.emit(self.recording_id)

    def on_next(self, image: Tuple[int, float, np.ndarray]):
        _, self.current_time, self.current_image = image
        self.image_signal.emit()

    def on_error(self, err):
        print(f"[CameraWidget] error: {err}")
        import traceback
        traceback.print_exc()

    def on_completed(self):
        print("[CameraWidget] completed")

    def display_image(self):
        if self.current_image is None:
            self.label.clear()
            self.label.setText("No image")
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
        time_str = time.strftime("%H:%M:%S", time.gmtime(self.current_time))
        self.lbl_time.setText(f"{time_str}")

    # -------- public -------------------------------------------------
    def attach(self, obs):
        self.dispose()

        self._sub = (
            obs.pipe(
                ops.observe_on(self._worker),
            )
            .subscribe(self)
        )
        return self._sub

    def dispose(self):
        if self._sub:
            self._sub.dispose()
            self._sub = None

    def resizeEvent(self, event):
        super(CameraWidget, self).resizeEvent(event)
        self.display_image()

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())
