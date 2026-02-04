from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit

from aaaflow3r.plugins.core.source.audio.audio_file.config import AudioFileSourceConfig


class AudioFileSourceConfigWidget(QWidget):
    def __init__(self, config: AudioFileSourceConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.txt_file_path = QLineEdit(self.config.file_path)

        self.layout = QFormLayout(self)
        self.layout.addRow("File Path", self.txt_file_path)
        self.setLayout(self.layout)

        self.txt_file_path.textChanged.connect(self._file_path_changed)

    def _file_path_changed(self, value: str):
        self.config.file_path = value
