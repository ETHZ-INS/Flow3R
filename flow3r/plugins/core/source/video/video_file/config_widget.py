from PySide6.QtWidgets import QWidget, QLineEdit, QFormLayout, QCheckBox

from flow3r.plugins.core.source.video.video_file.config import VideoFileSourceConfig


class VideoFileSourceConfigWidget(QWidget):
    def __init__(self, config: VideoFileSourceConfig, parent=None):
        super().__init__(parent)

        self.config = config

        layout = QFormLayout(self)

        self.txt_file_path = QLineEdit(self.config.file_path)
        layout.addRow("File Path", self.txt_file_path)

        self.chb_grayscale = QCheckBox()
        self.chb_grayscale.setChecked(self.config.grayscale)
        layout.addRow("Grayscale", self.chb_grayscale)

        self.chb_loop = QCheckBox()
        self.chb_loop.setChecked(self.config.loop)
        layout.addRow("Loop", self.chb_loop)

        self.setLayout(layout)

        self.txt_file_path.textChanged.connect(self._file_path_changed)
        self.chb_grayscale.stateChanged.connect(self._grayscale_changed)
        self.chb_loop.stateChanged.connect(self._loop_changed)

    def _file_path_changed(self, value: str):
        self.config.file_path = value

    def _grayscale_changed(self, state: int):
        self.config.grayscale = state != 0

    def _loop_changed(self, state: int):
        self.config.loop = state != 0
