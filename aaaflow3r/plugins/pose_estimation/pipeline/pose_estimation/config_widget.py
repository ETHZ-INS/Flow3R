from PySide6.QtWidgets import QWidget, QLineEdit, QFormLayout

from aaaflow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig
from aaaflow3r.plugins.pose_estimation.pipeline.pose_estimation.config import PoseEstimationConfig


class PoseEstimationConfigWidget(QWidget):
    def __init__(self, config: PoseEstimationConfig, parent=None):
        super().__init__(parent)

        self.config = config

        self.txt_video_file = QLineEdit(self.config.video_file)
        self.txt_pose_results_file = QLineEdit(self.config.pose_results_file)
        self.txt_pose_model_folder = QLineEdit(self.config.pose_model_folder)

        self.layout = QFormLayout(self)
        self.layout.addRow("Video File", self.txt_video_file)
        self.layout.addRow("Pose Results File", self.txt_pose_results_file)
        self.layout.addRow("Pose Model Folder", self.txt_pose_model_folder)
        self.setLayout(self.layout)

        self.txt_video_file.editingFinished.connect(self._video_file_changed)
        self.txt_pose_results_file.editingFinished.connect(self._pose_results_file_changed)
        self.txt_pose_model_folder.editingFinished.connect(self._pose_model_folder_changed)

    def _video_file_changed(self):
        value = self.txt_video_file.text()
        self.config.video_file = value

    def _pose_results_file_changed(self):
        value = self.txt_pose_results_file.text()
        self.config.pose_results_file = value

    def _pose_model_folder_changed(self):
        value = self.txt_pose_model_folder.text()
        self.config.pose_model_folder = value
