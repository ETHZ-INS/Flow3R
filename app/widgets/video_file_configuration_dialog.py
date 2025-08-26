from copy import deepcopy

from PySide6.QtWidgets import QDialog, QFileDialog

from app.config.save_video_config import SaveVideoConfig
from app.controller import Controller
from app.layout.video_file_configuration_dialog import Ui_VideoFileConfigurationDialog
from app.widgets.path_editor_dialog import TextEditorDialog


class VideoFileConfigurationDialog(Ui_VideoFileConfigurationDialog, QDialog):
    def __init__(self, controller: Controller, config: SaveVideoConfig, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.controller = controller
        self.config = deepcopy(config)
        self.variables = list(controller.config.variable_config_list.variables.values())

        self.dpd_codec.clear()
        for codec_name, codec_text in SaveVideoConfig.CODECS.items():
            self.dpd_codec.addItem(codec_text, codec_name)

        self.txt_filename.textChanged.connect(self.filename_changed)
        self.dpd_codec.currentIndexChanged.connect(self.codec_changed)

        self.btn_select_file.clicked.connect(self.select_file)
        self.btn_editor.clicked.connect(self.open_editor)

        self.update_form()

    def update_form(self):
        self.txt_filename.setText(self.config.file_path_template)
        self.lbl_filename_preview.setText(self.config.file_path_template)

    def select_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Video File")
        if file_path:
            self.txt_filename.setText(file_path)

    def open_editor(self):
        dialog = TextEditorDialog(self.controller, "Video File", self.txt_filename.text(), value_type="file", parent=self)
        if dialog.exec():
            self.txt_filename.setText(dialog.txt_value.text())

    def filename_changed(self):
        self.config.file_path_template = self.txt_filename.text().strip()

    def codec_changed(self):
        codec = self.dpd_codec.currentData()
        if codec:
            self.config.codec = codec
        else:
            self.config.codec = None
