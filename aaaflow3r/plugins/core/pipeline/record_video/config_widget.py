from PySide6.QtWidgets import QWidget, QLineEdit, QFormLayout

from aaaflow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig


class RecordVideoConfigWidget(QWidget):
    def __init__(self, config: RecordVideoConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.txt_file_path = QLineEdit(self.config.video_file)

        self.layout = QFormLayout(self)
        self.layout.addRow("File Path", self.txt_file_path)
        self.setLayout(self.layout)

        self.txt_file_path.textChanged.connect(self._video_file_changed)

    def _video_file_changed(self, value: str):
        self.config.video_file = value
