from copy import deepcopy

from PySide6.QtWidgets import QDialog

from app.config.pose_estimation_config import PoseEstimationConfig
from app.config.welfare_recorder_config import WelfareRecorderConfig
from app.layout.pose_estimation_configuration_dialog import Ui_PoseEstimationConfigurationDialog


class PoseEstimationConfigurationDialog(Ui_PoseEstimationConfigurationDialog, QDialog):
    def __init__(self, config: WelfareRecorderConfig, pose_estimation_config: PoseEstimationConfig = None, su_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.config = config
        self.pose_estimation_config = deepcopy(pose_estimation_config) if pose_estimation_config else PoseEstimationConfig()

        self.su_mode = su_mode

        placeholders = list(self.config.placeholders.values())
        placeholder_context = self.config.get_placeholder_context(preview=True)

        self.txt_save_file.set_mode("file")
        self.txt_save_file.setText(self.pose_estimation_config.save_file)
        self.txt_save_file.set_placeholders(placeholders)
        self.txt_save_file.set_placeholder_context(placeholder_context)

        self.dpd_preset.clear()
        for preset_id, preset_config in self.config.pose_estimation_presets.items():
            self.dpd_preset.addItem(preset_config.name, preset_id)

        self.dpd_preset.currentIndexChanged.connect(self.preset_changed)
        self.chb_save_file.stateChanged.connect(self.save_to_file_changed)
        self.txt_save_file.textChanged.connect(self.save_file_changed)

        self.update_all()

    def update_dpd_preset(self):
        self.dpd_preset.blockSignals(True)
        selected_index = self.dpd_preset.findData(self.pose_estimation_config.preset_id) if self.pose_estimation_config.preset_id else -1
        self.dpd_preset.setCurrentIndex(selected_index)
        self.dpd_preset.blockSignals(False)

        enabled = not self.pose_estimation_config.is_locked("preset_id") or self.su_mode
        self.dpd_preset.setEnabled(enabled)

    def update_chb_save_file(self):
        self.chb_save_file.blockSignals(True)
        self.chb_save_file.setChecked(self.pose_estimation_config.save_to_file)
        self.chb_save_file.blockSignals(False)

        enabled = not self.pose_estimation_config.is_locked("save_to_file") or self.su_mode
        self.chb_save_file.setEnabled(enabled)

    def update_txt_save_file(self):
        self.txt_save_file.blockSignals(True)
        self.txt_save_file.setText(self.pose_estimation_config.save_file)
        self.txt_save_file.blockSignals(False)

        enabled = not self.pose_estimation_config.is_locked("save_file") or self.su_mode
        self.txt_save_file.setEnabled(enabled)

    def update_all(self):
        self.update_dpd_preset()
        self.update_chb_save_file()
        self.update_txt_save_file()

    def preset_changed(self):
        self.pose_estimation_config.preset_id = self.dpd_preset.currentData()

    def save_to_file_changed(self):
        self.pose_estimation_config.save_to_file = self.chb_save_file.isChecked()

    def save_file_changed(self):
        self.pose_estimation_config.save_file = self.txt_save_file.text()
