from typing import Dict, Tuple, Any, cast

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget, QLineEdit, QFormLayout, QComboBox, QHBoxLayout, QToolButton, QCheckBox

from flow3r.core.api.app.app_context import IAppContext
from flow3r.plugins.homecage.pipeline.homecage_analysis.config import HomecageAnalysisConfig
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelsSettings


class HomecageAnalysisConfigWidget(QWidget):
    def __init__(self, app_context: IAppContext, config: HomecageAnalysisConfig, parent=None):
        super().__init__(parent)

        self.app_context = app_context
        self.config = config

        self.chb_use_3d_camera = QCheckBox("Use 3D Camera")
        self.chb_use_3d_camera.setChecked(self.config.use_3d_camera)

        self.txt_top_video_file = QLineEdit(self.config.top_video_file)
        self.txt_offset_video_file = QLineEdit(self.config.offset_video_file)
        self.txt_top_pose_results_file = QLineEdit(self.config.top_pose_results_file)
        self.txt_offset_pose_results_file = QLineEdit(self.config.offset_pose_results_file)
        self.txt_calibration_file = QLineEdit(self.config.calibration_file)
        self.txt_live_results_input_folder = QLineEdit(self.config.live_results_input_folder)

        self.app_context.settings_service.changed.connect(self._settings_changed)

        self.frm_mouse_pose_model = QWidget(self)
        frm_mouse_pose_model_layout = QHBoxLayout(self.frm_mouse_pose_model)
        frm_mouse_pose_model_layout.setContentsMargins(0, 0, 0, 0)

        self.dpd_mouse_pose_model = QComboBox(self.frm_mouse_pose_model)
        pose_estimation_models_settings = self.app_context.settings_service.get(("pose_estimation", "models"), PoseEstimationModelsSettings())
        for model_config in pose_estimation_models_settings.models.values():
            self.dpd_mouse_pose_model.addItem(model_config.name, model_config.id)
        self.dpd_mouse_pose_model.setCurrentIndex(self.dpd_mouse_pose_model.findData(self.config.mouse_pose_model_id))
        frm_mouse_pose_model_layout.addWidget(self.dpd_mouse_pose_model)

        self.btn_edit_mouse_pose_models = QToolButton(self.frm_mouse_pose_model)
        self.btn_edit_mouse_pose_models.setText("...")
        frm_mouse_pose_model_layout.addWidget(self.btn_edit_mouse_pose_models)

        self.frm_environment_pose_model = QWidget(self)
        frm_environment_pose_model_layout = QHBoxLayout(self.frm_environment_pose_model)
        frm_environment_pose_model_layout.setContentsMargins(0, 0, 0, 0)

        self.dpd_environment_pose_model = QComboBox(self.frm_environment_pose_model)
        pose_estimation_models_settings = self.app_context.settings_service.get(("pose_estimation", "models"), PoseEstimationModelsSettings())
        for model_config in pose_estimation_models_settings.models.values():
            self.dpd_environment_pose_model.addItem(model_config.name, model_config.id)
        self.dpd_environment_pose_model.setCurrentIndex(self.dpd_environment_pose_model.findData(self.config.environment_pose_model_id))
        frm_environment_pose_model_layout.addWidget(self.dpd_environment_pose_model)

        self.btn_edit_environment_pose_models = QToolButton(self.frm_environment_pose_model)
        self.btn_edit_environment_pose_models.setText("...")
        frm_environment_pose_model_layout.addWidget(self.btn_edit_environment_pose_models)

        self.layout = QFormLayout(self)
        self.layout.addRow("Use 3D Camera", self.chb_use_3d_camera)
        self.layout.addRow("Top Video File", self.txt_top_video_file)
        self.layout.addRow("Offset Video File", self.txt_offset_video_file)
        self.layout.addRow("Top Pose Results File", self.txt_top_pose_results_file)
        self.layout.addRow("Offset Pose Results File", self.txt_offset_pose_results_file)
        self.layout.addRow("Calibration File", self.txt_calibration_file)
        self.layout.addRow("Live Results Input Folder", self.txt_live_results_input_folder)
        self.layout.addRow("Mouse Pose Model", self.frm_mouse_pose_model)
        self.layout.addRow("Environment Pose Model", self.frm_environment_pose_model)
        
        self.setLayout(self.layout)

        self.btn_edit_mouse_pose_models.clicked.connect(self._edit_pose_models)
        self.btn_edit_environment_pose_models.clicked.connect(self._edit_pose_models)
        self.chb_use_3d_camera.stateChanged.connect(self._use_3d_camera_changed)
        self.txt_top_video_file.editingFinished.connect(self._top_video_file_changed)
        self.txt_offset_video_file.editingFinished.connect(self._offset_video_file_changed)
        self.txt_top_pose_results_file.editingFinished.connect(self._top_pose_results_file_changed)
        self.txt_offset_pose_results_file.editingFinished.connect(self._offset_pose_results_file_changed)
        self.txt_calibration_file.editingFinished.connect(self._calibration_file_changed)
        self.txt_live_results_input_folder.editingFinished.connect(self._live_results_input_folder_changed)
        self.dpd_mouse_pose_model.currentIndexChanged.connect(self._mouse_pose_model_changed)
        self.dpd_environment_pose_model.currentIndexChanged.connect(self._environment_pose_model_changed)

    def _edit_pose_models(self):
        self.app_context.navigator_service.open(("Pose Estimation", "Pose Estimation Models"))

    def _use_3d_camera_changed(self, checked: bool):
        self.config.use_3d_camera = checked

    def _top_video_file_changed(self):
        value = self.txt_top_video_file.text()
        self.config.top_video_file = value

    def _offset_video_file_changed(self):
        value = self.txt_offset_video_file.text()
        self.config.offset_video_file = value

    def _top_pose_results_file_changed(self):
        value = self.txt_top_pose_results_file.text()
        self.config.top_pose_results_file = value

    def _offset_pose_results_file_changed(self):
        value = self.txt_offset_pose_results_file.text()
        self.config.offset_pose_results_file = value

    def _calibration_file_changed(self):
        value = self.txt_calibration_file.text()
        self.config.calibration_file = value

    def _live_results_input_folder_changed(self):
        value = self.txt_live_results_input_folder.text()
        self.config.live_results_input_folder = value

    def _mouse_pose_model_changed(self):
        model_id = self.dpd_mouse_pose_model.itemData(self.dpd_mouse_pose_model.currentIndex())
        self.config.mouse_pose_model_id = model_id

    def _environment_pose_model_changed(self):
        model_id = self.dpd_environment_pose_model.itemData(self.dpd_environment_pose_model.currentIndex())
        self.config.environment_pose_model_id = model_id

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

        self.dpd_environment_pose_model.clear()
        for model_config in pose_estimation_models_settings.models.values():
            self.dpd_environment_pose_model.addItem(model_config.name, model_config.id)
        self.dpd_environment_pose_model.setCurrentIndex(self.dpd_environment_pose_model.findData(self.config.environment_pose_model_id))
