import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QDockWidget

from app.layout.camera_widget import Ui_CameraWidget


class CameraWidget(Ui_CameraWidget, QDockWidget):
    def __init__(self, camera_name: str = "Unnamed Camera"):
        super(CameraWidget, self).__init__()

        self.setupUi(self)

        self.camera_name = camera_name
        self.setWindowTitle(self.camera_name)

        self.label.setMinimumSize(20, 20)

        self.current_image = None

    def set_image(self, image: np.ndarray):
        self.current_image = image

        label_width = self.label.width()
        label_height = self.label.height()

        image_height, image_width, _ = image.shape

        scale = min(label_width / image_width, label_height / image_height)
        new_width = int(image_width * scale)
        new_height = int(image_height * scale)
        resized_image = cv2.resize(image, (new_width, new_height))

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
        # Recalculate the image size when the widget is resized
        if hasattr(self, 'current_image'):
            self.set_image(self.current_image)