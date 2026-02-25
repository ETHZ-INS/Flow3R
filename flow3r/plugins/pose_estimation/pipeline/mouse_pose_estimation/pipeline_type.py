from typing import Callable

from PySide6.QtWidgets import QWidget

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.pipeline.abc.pipeline_type import IPipelineType
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.config import MousePoseEstimationConfig
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.config_widget import MousePoseEstimationConfigWidget
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.pipeline import MousePoseEstimationPipeline


class MousePoseEstimationPipelineType(IPipelineType[MousePoseEstimationConfig, MousePoseEstimationPipeline]):
    @property
    def name(self) -> str:
        return "Mouse Pose Estimation"

    def get_config_factory(self) -> Callable[[], MousePoseEstimationConfig]:
        return MousePoseEstimationConfig

    def get_config_widget_factory(self) -> Callable[[IAppContext, MousePoseEstimationConfig, QWidget], QWidget]:
        return MousePoseEstimationConfigWidget

    def get_pipeline_factory(self) -> Callable[[], MousePoseEstimationPipeline]:
        return MousePoseEstimationPipeline
