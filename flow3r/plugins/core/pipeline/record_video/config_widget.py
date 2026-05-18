from PySide6.QtWidgets import QWidget, QFormLayout, QComboBox, QVBoxLayout, QMessageBox, QSizePolicy, QLabel

from core.widgets.placeholder_line_edit import PlaceholderTextWidget
from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.widgets.collapsible_section import CollapsibleSection
from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.core.widgets.path_input import PathWidget
from flow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig


class RecordVideoConfigWidget(IConfigWidget):
    def __init__(self, app_context: IAppContext, config: RecordVideoConfig, parent=None):
        super().__init__(parent)

        self.config = config
        self._app_context = app_context

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.frm_settings = QWidget()
        self.frm_settings_layout = QFormLayout(self.frm_settings)
        self.layout.addWidget(self.frm_settings)

        self.txt_file_path = PlaceholderTextWidget(mode="file")
        self.txt_file_path.setText(self.config.video_file)
        self.frm_settings_layout.addRow("Video File", self.txt_file_path.input_row)
        self.frm_settings_layout.addRow(QLabel(""), self.txt_file_path.lbl_preview)
        self.frm_settings_layout.labelForField(self.txt_file_path.lbl_preview).setVisible(False)
        self.txt_file_path.editingFinished.connect(self._video_file_changed)
        self.txt_file_path.set_placeholder_service(app_context.placeholder_service)

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

    def get_config(self) -> RecordVideoConfig:
        return self.config

    def _video_file_changed(self):
        value = self.txt_file_path.text()
        self.config.video_file = value

    def _video_quality_changed(self):
        video_quality = self.dpd_video_quality.currentData()

        if video_quality == "high":
            QMessageBox.warning(self, "Warning", "High video quality may cause performance issues, especially if you record multiple videos at the same time", QMessageBox.StandardButton.Ok)

        self.config.video_quality = video_quality
