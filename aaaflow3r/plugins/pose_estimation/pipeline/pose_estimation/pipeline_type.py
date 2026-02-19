from typing import Callable

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.pipeline.abc.pipeline_type import IPipelineType
from aaaflow3r.plugins.pose_estimation.pipeline.pose_estimation.config import PoseEstimationConfig
from aaaflow3r.plugins.pose_estimation.pipeline.pose_estimation.config_widget import PoseEstimationConfigWidget
from aaaflow3r.plugins.pose_estimation.pipeline.pose_estimation.pipeline import PoseEstimationPipeline


class PoseEstimationPipelineType(IPipelineType[PoseEstimationConfig, PoseEstimationPipeline]):
    @property
    def name(self) -> str:
        return "Pose Estimation"

    def get_config_factory(self) -> Callable[[], PoseEstimationConfig]:
        return PoseEstimationConfig

    def get_config_widget_factory(self) -> Callable[[IAppContext, PoseEstimationConfig, QWidget], QWidget]:
        return PoseEstimationConfigWidget

    def get_pipeline_factory(self) -> Callable[[], PoseEstimationPipeline]:
        return PoseEstimationPipeline
