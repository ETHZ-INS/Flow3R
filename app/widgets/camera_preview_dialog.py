import cv2
import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDialog

from app.layout.camera_preview_dialog import Ui_CameraPreviewDialog


class CameraPreviewDialog(Ui_CameraPreviewDialog, QDialog):
    image_signal = Signal()

    def __init__(self, camera_widget):
        super(CameraPreviewDialog, self).__init__(camera_widget)

        self.setupUi(self)

        self.image_signal.connect(self.display_image)

        self.current_image = None
        self.current_fps = 0.0
        self.error_message = None

    def set_image(self, image: np.ndarray):
        self.current_image = image
        self.image_signal.emit()

    def set_fps(self, fps: float):
        self.current_fps = fps
        self.image_signal.emit()

    def set_error(self, error_message: str = None):
        self.error_message = error_message
        self.image_signal.emit()

    def display_image(self):
        if self.error_message is not None:
            self.label.clear()
            self.label.setText(self.error_message)
            return

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

        if self.current_fps is not None:
            cv2.putText(resized_image, f"{self.current_fps:.2f} FPS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

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
        super(CameraPreviewDialog, self).resizeEvent(event)
        self.display_image()
