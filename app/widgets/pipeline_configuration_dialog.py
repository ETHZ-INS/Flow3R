from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QProgressDialog, QMessageBox, QDialogButtonBox

from app.config.pipeline_config import PipelineConfig
from app.layout.pipeline_configuration_dialog import Ui_PipelineConfigurationDialog
from app.controller import Controller
from app.widgets.pose_estimation_configuration_dialog import PoseEstimationConfigurationDialog
from app.widgets.video_file_configuration_dialog import VideoFileConfigurationDialog


class PipelineConfigurationDialog(Ui_PipelineConfigurationDialog, QDialog):
    def __init__(self, controller: Controller, selected_camera_id: str = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        print(controller.config.camera_config_list.cameras)
        if len(controller.config.camera_config_list.cameras) == 0:
            raise Exception("No cameras found in configuration.")

        self.controller = controller
        self.pipeline_config_list = deepcopy(controller.config.pipeline_config_list)

        self.chb_live_heatmap.setVisible(False)
        self.btn_configure_live_heatmap.setVisible(False)

        self.chb_welfare_analysis.setVisible(False)
        self.btn_configure_welfare_analysis.setVisible(False)

        self.chb_grimace.setVisible(False)
        self.btn_configure_grimace.setVisible(False)

        self.dpd_camera.clear()
        for camera_id, camera in self.controller.config.camera_config_list.cameras.items():
            if camera_id not in self.pipeline_config_list.pipelines:
                self.pipeline_config_list.pipelines[camera_id] = PipelineConfig(camera_id)
            self.dpd_camera.addItem(camera.camera_name, userData=camera_id)
        self.dpd_camera.setCurrentIndex(0)

        self.current_camera_id = self.dpd_camera.currentData()
        self.current_pipeline = self.pipeline_config_list.pipelines[self.current_camera_id]

        self.dpd_camera.currentIndexChanged.connect(self.current_camera_changed)

        self.chb_save_video.stateChanged.connect(self.save_video_changed)
        self.chb_pose_estimation.stateChanged.connect(self.pose_estimation_changed)

        self.btn_configure_save_video.clicked.connect(self.configure_save_video)
        self.btn_configure_pose_estimation.clicked.connect(self.configure_pose_estimation)

        self.dpd_camera.blockSignals(True)
        if selected_camera_id and selected_camera_id in self.controller.config.camera_config_list.cameras:
            self.dpd_camera.setCurrentIndex(self.dpd_camera.findData(selected_camera_id))
        else:
            self.dpd_camera.setCurrentIndex(0)
        self.dpd_camera.blockSignals(False)

        self.update_form()

    def update_form(self):
        self.chb_save_video.setChecked(self.current_pipeline.save_video)
        self.chb_pose_estimation.setChecked(self.current_pipeline.pose_estimation)

    def current_camera_changed(self):
        camera_id = self.dpd_camera.currentData()
        if camera_id is None:
            self.dpd_camera.setCurrentIndex(0)
        camera_id = self.dpd_camera.currentData()

        if camera_id == self.current_camera_id:
            return

        self.current_camera_id = camera_id
        self.current_pipeline = self.pipeline_config_list.pipelines[self.current_camera_id]
        self.update_form()

    def save_video_changed(self):
        self.current_pipeline.save_video = self.chb_save_video.isChecked()
        self.update_form()

    def pose_estimation_changed(self):
        self.current_pipeline.pose_estimation = self.chb_pose_estimation.isChecked()
        self.update_form()

    def configure_save_video(self):
        dialog = VideoFileConfigurationDialog(self.controller, self.current_pipeline.save_video_config, parent=self)
        if dialog.exec_():
            self.current_pipeline.save_video_config = dialog.config
            print("Video file configuration saved.")
        self.update_form()

    def configure_pose_estimation(self):
        dialog = PoseEstimationConfigurationDialog(self.controller, self.current_pipeline.pose_estimation_config, self)
        if dialog.exec_():
            self.current_pipeline.pose_estimation_config = dialog.config
            print("Pose estimation configuration saved.")
        self.update_form()

    def accept(self):
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setEnabled(False)

        futures = []
        for pipeline_config in self.pipeline_config_list.pipelines.values():
            if pipeline_config.camera_id not in self.controller.config.pipeline_config_list.pipelines:
                raise Exception(f"Camera {pipeline_config.camera_id} not found in pipeline configuration list.")
            elif pipeline_config != self.controller.config.pipeline_config_list.pipelines[pipeline_config.camera_id]:
                futures.append(self.controller.update_pipeline.future(pipeline_config))

        if not futures:
            super().accept()
            return

        success = True
        progress = QProgressDialog("Applying camera configuration...", None, 0, len(futures), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        for future in futures:
            if future.exception():
                QMessageBox.critical(self, "Camera Configuration Error", f"Error applying configuration: {future.exception()}")
                success = False
                continue
            res = future.result()
            if not res.success:
                QMessageBox.critical(self, "Camera Configuration Error", f"Error applying configuration: {res.message}")
                success = False
                continue
            progress.setValue(progress.value() + 1)

        if success:
            super().accept()
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setEnabled(True)
