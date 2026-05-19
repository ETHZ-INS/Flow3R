from typing import Callable

from PySide6.QtWidgets import QWidget

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.pipeline.abc.pipeline_type import IPipelineType
from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.config import MousePoseEstimationConfig
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.config_widget import MousePoseEstimationConfigWidget
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.pipeline import MousePoseEstimationPipeline


class MousePoseEstimationPipelineType(IPipelineType[MousePoseEstimationConfig, MousePoseEstimationPipeline]):
    @property
    def name(self) -> str:
        return "Mouse Pose Estimation"

    @property
    def config_factory(self) -> Callable[[], MousePoseEstimationConfig]:
        return MousePoseEstimationConfig

    @property
    def config_widget_factory(self) -> Callable[[IAppContext, MousePoseEstimationConfig, QWidget], IConfigWidget]:
        return MousePoseEstimationConfigWidget

    @property
    def pipeline_factory(self) -> Callable[[], MousePoseEstimationPipeline]:
        return MousePoseEstimationPipeline
