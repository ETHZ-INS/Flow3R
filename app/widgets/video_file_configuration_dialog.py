from copy import deepcopy

from PySide6.QtWidgets import QDialog

from app.config.save_video_config import SaveVideoConfig
from app.layout.video_file_configuration_dialog import Ui_VideoFileConfigurationDialog


class VideoFileConfigurationDialog(Ui_VideoFileConfigurationDialog, QDialog):
    def __init__(self, config: SaveVideoConfig, parent=None):
        # TODO: How to pass variable context (base folder, camera name...) to preview file name?
        super().__init__(parent)
        self.setupUi(self)

        self.config = deepcopy(config)

        self.dpd_codec.clear()
        for codec_name, codec_text in SaveVideoConfig.CODECS.items():
            self.dpd_codec.addItem(codec_text, codec_name)

        self.txt_filename.textChanged.connect(self.filename_changed)
        self.dpd_codec.currentIndexChanged.connect(self.codec_changed)

        self.update_form()

    def update_form(self):
        self.txt_filename.setText(self.config.file_path_template)
        self.lbl_filename_preview.setText(self.config.file_path_template)

    def filename_changed(self):
        self.config.file_path_template = self.txt_filename.text().strip()

    def codec_changed(self):
        codec = self.dpd_codec.currentData()
        if codec:
            self.config.codec = codec
        else:
            self.config.codec = None
