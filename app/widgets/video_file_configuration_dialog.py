from copy import deepcopy

from PySide6.QtWidgets import QDialog

from app.config.save_video_config import SaveVideoConfig
from app.config.welfare_recorder_config import  WelfareRecorderConfig
from app.layout.video_file_configuration_dialog import Ui_VideoFileConfigurationDialog


class VideoFileConfigurationDialog(Ui_VideoFileConfigurationDialog, QDialog):
    def __init__(self, config: WelfareRecorderConfig, save_video_config: SaveVideoConfig = None, su_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.config = config
        self.save_video_config = deepcopy(save_video_config) if save_video_config else SaveVideoConfig()

        self.su_mode = su_mode

        placeholders = list(self.config.placeholders.values())
        placeholder_context = self.config.get_placeholder_context(preview=True)

        self.txt_filename.set_mode("file")
        self.txt_filename.setText(self.save_video_config.file_path)
        self.txt_filename.set_placeholders(placeholders)
        self.txt_filename.set_placeholder_context(placeholder_context)

        self.dpd_codec.clear()
        for codec_name, codec_text in SaveVideoConfig.CODECS.items():
            self.dpd_codec.addItem(codec_text, codec_name)

        self.txt_filename.textChanged.connect(self.filename_changed)
        self.dpd_codec.currentIndexChanged.connect(self.codec_changed)

        self.update_all()

    def update_txt_filename(self):
        placeholder_context = self.config.get_placeholder_context(preview=True)
        self.txt_filename.set_placeholder_context(placeholder_context)
        self.txt_filename.setText(self.save_video_config.file_path)

        enabled = not self.save_video_config.is_locked("file_path") or self.su_mode
        self.txt_filename.setEnabled(enabled)

    def update_dpd_codec(self):
        index = self.dpd_codec.findData(self.save_video_config.video_codec) if self.save_video_config.video_codec else -1
        self.dpd_codec.setCurrentIndex(index)

        enabled = not self.save_video_config.is_locked("video_codec") or self.su_mode
        self.dpd_codec.setEnabled(enabled)

    def update_all(self):
        self.update_txt_filename()
        self.update_dpd_codec()

    def filename_changed(self):
        self.save_video_config.file_path = self.txt_filename.text().strip()

    def codec_changed(self):
        codec = self.dpd_codec.currentData()
        if codec:
            self.save_video_config.codec = codec
