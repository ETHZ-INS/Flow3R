from PySide6.QtWidgets import QLineEdit, QFormLayout, QCheckBox

from core.widgets.path_input import PathWidget
from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.plugins.core.source.video.video_file.config import VideoFileSourceConfig


class VideoFileSourceConfigWidget(IConfigWidget):
    def __init__(self, config: VideoFileSourceConfig, parent=None):
        super().__init__(parent)

        self.config = config

        layout = QFormLayout(self)

        self.txt_file_path = PathWidget(mode="file")
        self.txt_file_path.set_path(self.config.file_path if self.config.file_path else "")
        layout.addRow("File Path", self.txt_file_path)

        self.chb_grayscale = QCheckBox()
        self.chb_grayscale.setChecked(self.config.grayscale)
        layout.addRow("Grayscale", self.chb_grayscale)

        self.chb_loop = QCheckBox()
        self.chb_loop.setChecked(self.config.loop)
        layout.addRow("Loop", self.chb_loop)

        self.setLayout(layout)

        self.txt_file_path.path_changed.connect(self._file_path_changed)
        self.chb_grayscale.stateChanged.connect(self._grayscale_changed)
        self.chb_loop.stateChanged.connect(self._loop_changed)

    def get_config(self) -> VideoFileSourceConfig:
        return self.config

    def _file_path_changed(self, value: str):
        self.config.file_path = value

    def _grayscale_changed(self, state: int):
        self.config.grayscale = state != 0

    def _loop_changed(self, state: int):
        self.config.loop = state != 0
