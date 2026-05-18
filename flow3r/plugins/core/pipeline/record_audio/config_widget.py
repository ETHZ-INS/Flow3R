from PySide6.QtWidgets import QLineEdit, QFormLayout

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.plugins.core.pipeline.record_audio.config import RecordAudioConfig


class RecordAudioConfigWidget(IConfigWidget):
    def __init__(self, app_context: IAppContext, config: RecordAudioConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.txt_file_path = QLineEdit(self.config.audio_file)

        self.layout = QFormLayout(self)
        self.layout.addRow("File Path", self.txt_file_path)
        self.setLayout(self.layout)

        self.txt_file_path.textChanged.connect(self._audio_file_changed)

    def get_config(self) -> RecordAudioConfig:
        return self.config

    def _audio_file_changed(self, value: str):
        self.config.audio_file = value
