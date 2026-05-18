from PySide6.QtWidgets import QLineEdit, QFormLayout

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.plugins.core.pipeline.record_video_with_audio.config import RecordVideoWithAudioConfig


class RecordVideoWithAudioConfigWidget(IConfigWidget):
    def __init__(self, app_context: IAppContext, config: RecordVideoWithAudioConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.txt_file_path = QLineEdit(self.config.video_file)

        self.layout = QFormLayout(self)
        self.layout.addRow("File Path", self.txt_file_path)
        self.setLayout(self.layout)

        self.txt_file_path.textChanged.connect(self._video_file_changed)

    def get_config(self) -> RecordVideoWithAudioConfig:
        return self.config

    def _video_file_changed(self, value: str):
        self.config.video_file = value
