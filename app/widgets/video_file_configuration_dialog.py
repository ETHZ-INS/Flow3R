from copy import deepcopy

from PySide6.QtWidgets import QDialog

from app.config.save_video_config import SaveVideoConfig
from app.controller import Controller
from app.layout.video_file_configuration_dialog import Ui_VideoFileConfigurationDialog


class VideoFileConfigurationDialog(Ui_VideoFileConfigurationDialog, QDialog):
    def __init__(self, controller: Controller, config: SaveVideoConfig, recording_id: str = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.config = deepcopy(config)
        self.recording_id = recording_id

        self.txt_filename.set_mode("file")
        self.txt_filename.setText(self.config.file_path)
        self.txt_filename.set_config(self.controller.get_config())

        self.dpd_codec.clear()
        for codec_name, codec_text in SaveVideoConfig.CODECS.items():
            self.dpd_codec.addItem(codec_text, codec_name)

        self.txt_filename.textChanged.connect(self.filename_changed)
        self.dpd_codec.currentIndexChanged.connect(self.codec_changed)

    def filename_changed(self):
        self.config.file_path = self.txt_filename.text().strip()

    def codec_changed(self):
        codec = self.dpd_codec.currentData()
        if codec:
            self.config.codec = codec
        else:
            self.config.codec = None
