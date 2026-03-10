from typing import Dict, Tuple, Any, cast

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget, QLineEdit, QFormLayout, QComboBox, QHBoxLayout, QToolButton

from flow3r.core.api.app.app_context import IAppContext
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.config import MousePoseEstimationConfig
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelsSettings


class MousePoseEstimationConfigWidget(QWidget):
    def __init__(self, app_context: IAppContext, config: MousePoseEstimationConfig, parent=None):
        super().__init__(parent)

        self.app_context = app_context
        self.config = config

        self.txt_video_file = QLineEdit(self.config.video_file)
        self.txt_pose_results_file = QLineEdit(self.config.pose_results_file)

        self.app_context.settings_service.changed.connect(self._settings_changed)

        self.frm_mouse_pose_model = QWidget(self)
        frm_pose_model_layout = QHBoxLayout(self.frm_mouse_pose_model)
        frm_pose_model_layout.setContentsMargins(0, 0, 0, 0)

        self.dpd_mouse_pose_model = QComboBox(self.frm_mouse_pose_model)
        pose_estimation_models_settings = self.app_context.settings_service.get(("pose_estimation", "models"), PoseEstimationModelsSettings())
        for model_config in pose_estimation_models_settings.models.values():
            self.dpd_mouse_pose_model.addItem(model_config.name, model_config.id)
        self.dpd_mouse_pose_model.setCurrentIndex(self.dpd_mouse_pose_model.findData(self.config.mouse_pose_model_id))
        frm_pose_model_layout.addWidget(self.dpd_mouse_pose_model)

        self.btn_edit_mouse_pose_models = QToolButton(self.frm_mouse_pose_model)
        self.btn_edit_mouse_pose_models.setText("...")
        frm_pose_model_layout.addWidget(self.btn_edit_mouse_pose_models)

        self.frm_env_pose_model = QWidget(self)
        frm_pose_model_layout = QHBoxLayout(self.frm_env_pose_model)
        frm_pose_model_layout.setContentsMargins(0, 0, 0, 0)

        self.dpd_env_pose_model = QComboBox(self.frm_env_pose_model)
        pose_estimation_models_settings = self.app_context.settings_service.get(("pose_estimation", "models"), PoseEstimationModelsSettings())
        for model_config in pose_estimation_models_settings.models.values():
            self.dpd_env_pose_model.addItem(model_config.name, model_config.id)
        self.dpd_env_pose_model.setCurrentIndex(self.dpd_env_pose_model.findData(self.config.env_pose_model_id))
        frm_pose_model_layout.addWidget(self.dpd_env_pose_model)

        self.btn_edit_env_pose_models = QToolButton(self.frm_env_pose_model)
        self.btn_edit_env_pose_models.setText("...")
        frm_pose_model_layout.addWidget(self.btn_edit_env_pose_models)

        self.layout = QFormLayout(self)
        self.layout.addRow("Video File", self.txt_video_file)
        self.layout.addRow("Pose Results File", self.txt_pose_results_file)
        self.layout.addRow("Mouse Model", self.frm_mouse_pose_model)
        self.layout.addRow("Environment Model", self.frm_env_pose_model)
        self.setLayout(self.layout)

        self.btn_edit_mouse_pose_models.clicked.connect(self._edit_pose_models)
        self.btn_edit_env_pose_models.clicked.connect(self._edit_pose_models)
        self.txt_video_file.editingFinished.connect(self._video_file_changed)
        self.txt_pose_results_file.editingFinished.connect(self._pose_results_file_changed)
        self.dpd_mouse_pose_model.currentIndexChanged.connect(self._mouse_pose_model_changed)
        self.dpd_env_pose_model.currentIndexChanged.connect(self._env_pose_model_changed)

    def _edit_pose_models(self):
        self.app_context.navigator_service.open(("Pose Estimation", "Pose Estimation Models"), parent=self)

    def _video_file_changed(self):
        value = self.txt_video_file.text()
        self.config.video_file = value

    def _pose_results_file_changed(self):
        value = self.txt_pose_results_file.text()
        self.config.pose_results_file = value

    def _mouse_pose_model_changed(self):
        model_id = self.dpd_mouse_pose_model.itemData(self.dpd_mouse_pose_model.currentIndex())
        self.config.mouse_pose_model_id = model_id

    def _env_pose_model_changed(self):
        model_id = self.dpd_env_pose_model.itemData(self.dpd_env_pose_model.currentIndex())
        self.config.env_pose_model_id = model_id

    @Slot(object)
    def _settings_changed(self, patch: Dict[Tuple[str, ...], Any]):
        pose_estimation_models_settings = patch.get(("pose_estimation", "models"))
        if not pose_estimation_models_settings:
            return
        pose_estimation_models_settings = cast(PoseEstimationModelsSettings, pose_estimation_models_settings)

        self.dpd_mouse_pose_model.clear()
        for model_config in pose_estimation_models_settings.models.values():
            self.dpd_mouse_pose_model.addItem(model_config.name, model_config.id)
        self.dpd_mouse_pose_model.setCurrentIndex(self.dpd_mouse_pose_model.findData(self.config.mouse_pose_model_id))

        self.dpd_env_pose_model.clear()
        for model_config in pose_estimation_models_settings.models.values():
            self.dpd_env_pose_model.addItem(model_config.name, model_config.id)
        self.dpd_env_pose_model.setCurrentIndex(self.dpd_env_pose_model.findData(self.config.env_pose_model_id))
