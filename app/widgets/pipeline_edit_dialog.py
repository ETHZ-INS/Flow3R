from concurrent.futures import Future
from copy import deepcopy
from typing import List

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QMessageBox, QLayout

from app.config.pipeline_config import PipelineConfig
from app.controller import Controller
from app.layout.pipeline_edit_dialog import Ui_PipelineEditDialog
from app.thread_bound_callable import thread_bound
from app.widgets.pose_estimation_configuration_dialog import PoseEstimationConfigurationDialog
from app.widgets.video_file_configuration_dialog import VideoFileConfigurationDialog


class PipelineEditDialog(Ui_PipelineEditDialog, QDialog):
    def __init__(self, controller: Controller, pipeline: PipelineConfig = None, su_mode: bool = False, location: List[str] = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.frm_configuration.setMinimumWidth(400)

        self.chb_live_heatmap.setVisible(False)
        self.btn_configure_live_heatmap.setVisible(False)
        self.lbl_live_heatmap_hint.setVisible(False)

        self.chb_welfare_analysis.setVisible(False)
        self.btn_configure_welfare_analysis.setVisible(False)
        self.lbl_welfare_analysis_hint.setVisible(False)

        self.chb_grimace.setVisible(False)
        self.btn_configure_grimace.setVisible(False)

        self.controller = controller
        self.new = pipeline is None

        self.config = controller.get_config()

        if pipeline:
            self.pipeline = deepcopy(pipeline)
        else:
            default_pipeline = self.config.pipelines.get("default")
            if default_pipeline is None:
                self.pipeline = PipelineConfig()
            else:
                new_pipeline = PipelineConfig()
                self.pipeline = deepcopy(default_pipeline)
                self.pipeline.pipeline_id = new_pipeline.pipeline_id
                self.pipeline.pipeline_name = new_pipeline.pipeline_name

        self.su_mode = su_mode

        self.txt_name.editingFinished.connect(self.name_changed)

        self.chb_save_video.stateChanged.connect(self.save_video_changed)
        self.chb_pose_estimation.stateChanged.connect(self.pose_estimation_changed)

        self.btn_configure_save_video.clicked.connect(self.configure_save_video)
        self.btn_configure_pose_estimation.clicked.connect(self.configure_pose_estimation)

        self.update_all()

        if location:
            if location[0] == "save_video":
                QTimer.singleShot(0, self.configure_save_video)
            elif location[0] == "pose_estimation":
                QTimer.singleShot(0, self.configure_pose_estimation)

    def update_txt_name(self):
        enabled = self.su_mode or (not self.pipeline.is_default and not self.pipeline.is_locked("pipeline_name"))
        self.txt_name.setEnabled(enabled)
        self.txt_name.setText(self.pipeline.pipeline_name)

    def update_chb_save_video(self):
        enabled = self.su_mode or not self.pipeline.is_locked("save_video")
        self.chb_save_video.setEnabled(enabled)
        self.chb_save_video.setChecked(self.pipeline.save_video)

    def update_chb_pose_estimation(self):
        enabled = self.su_mode or not self.pipeline.is_locked("pose_estimation")
        self.chb_pose_estimation.setEnabled(enabled)
        self.chb_pose_estimation.setChecked(self.pipeline.pose_estimation)

    def update_all(self):
        self.update_txt_name()
        self.update_chb_save_video()
        self.update_chb_pose_estimation()

    def name_changed(self):
        old_name = self.pipeline.pipeline_name
        existing_names = [p.pipeline_name for p in self.config.pipelines.values() if p.pipeline_id != self.pipeline.pipeline_id]

        base_name = self.txt_name.text().strip()
        attempt = 1
        while True:
            postfix = f" ({attempt})" if attempt > 1 else ""
            name = base_name + postfix
            if name and name not in existing_names:
                break
            attempt += 1

        if name == old_name:
            return

        if name != base_name:
            self.txt_name.blockSignals(True)
            self.txt_name.setText(name)
            self.txt_name.blockSignals(False)

        self.pipeline.pipeline_name = name

    def save_video_changed(self):
        self.pipeline.save_video = self.chb_save_video.isChecked()

    def pose_estimation_changed(self):
        self.pipeline.pose_estimation = self.chb_pose_estimation.isChecked()

    def configure_save_video(self):
        dialog = VideoFileConfigurationDialog(self.config, self.pipeline.save_video_config, parent=self)
        if dialog.exec_():
            print(dialog.save_video_config)
            self.pipeline.save_video_config = dialog.save_video_config
            print("Video file configuration saved.")
        self.update_all()

    def configure_pose_estimation(self):
        dialog = PoseEstimationConfigurationDialog(self.config, self.pipeline.pose_estimation_config, su_mode=self.su_mode, parent=self)
        if dialog.exec_():
            self.pipeline.pose_estimation_config = dialog.pose_estimation_config
            print("Pose estimation configuration saved.")
        self.update_all()

    def accept(self):
        if self.new:
            fut = self.controller.add_pipeline.future(self.pipeline)
        else:
            fut = self.controller.update_pipeline.future(self.pipeline)

        fut.add_done_callback(self._config_change_result.future)

    @thread_bound(timeout_ms=2000)
    def _config_change_result(self, fut: Future):
        if fut.exception():
            QMessageBox.critical(self, "Error", f"Error while saving configuration: {fut.exception()}")
            return
        super().accept()
