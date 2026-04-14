from PySide6.QtWidgets import QWidget, QFormLayout, QComboBox, QVBoxLayout

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.widgets.collapsible_section import CollapsibleSection
from flow3r.core.widgets.path_input import PathWidget
from flow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig


class RecordVideoConfigWidget(QWidget):
    def __init__(self, app_context: IAppContext, config: RecordVideoConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.frm_settings = QWidget()
        self.frm_settings_layout = QFormLayout(self.frm_settings)
        self.layout.addWidget(self.frm_settings)

        self.txt_file_path = PathWidget(mode="file")
        self.txt_file_path.set_path(self.config.video_file)
        self.frm_settings_layout.addRow("Video File", self.txt_file_path)
        self.txt_file_path.path_changed.connect(self._video_file_changed)

        frm_advanced_settings = QWidget()
        frm_advanced_settings_layout = QFormLayout(frm_advanced_settings)

        section = CollapsibleSection("Additional Settings")
        section.setWidget(frm_advanced_settings)
        self.layout.addWidget(section)

        self.dpd_video_quality = QComboBox()
        for key, value in RecordVideoConfig.QUALITY_CHOICES.items():
            self.dpd_video_quality.addItem(value, key)
        self.dpd_video_quality.setCurrentText(RecordVideoConfig.QUALITY_CHOICES[self.config.video_quality])
        frm_advanced_settings_layout.addRow("Video Quality", self.dpd_video_quality)
        self.dpd_video_quality.currentTextChanged.connect(self._video_quality_changed)

    def _video_file_changed(self, value: str):
        self.config.video_file = value

    def _video_quality_changed(self):
        self.config.video_quality = self.dpd_video_quality.currentData()
        print(f"Video quality changed to {self.config.video_quality}")
