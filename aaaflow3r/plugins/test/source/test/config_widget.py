from PySide6.QtWidgets import QWidget, QLineEdit, QFormLayout

from aaaflow3r.plugins.test.source.test.config import VideoTestSourceConfig


class VideoTestSourceConfigWidget(QWidget):
    def __init__(self, _config: VideoTestSourceConfig, parent=None):
        super().__init__(parent)
