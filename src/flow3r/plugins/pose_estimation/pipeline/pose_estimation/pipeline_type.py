from typing import Callable

from PySide6.QtWidgets import QWidget

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.pipeline.abc.pipeline_type import IPipelineType
from flow3r.core.widgets.config_widget import IConfigWidget
from flow3r.plugins.pose_estimation.pipeline.pose_estimation.config import PoseEstimationConfig
from flow3r.plugins.pose_estimation.pipeline.pose_estimation.config_widget import PoseEstimationConfigWidget
from flow3r.plugins.pose_estimation.pipeline.pose_estimation.pipeline import PoseEstimationPipeline


class PoseEstimationPipelineType(IPipelineType[PoseEstimationConfig, PoseEstimationPipeline]):
    @property
    def name(self) -> str:
        return "Pose Estimation"

    @property
    def config_factory(self) -> Callable[[], PoseEstimationConfig]:
        return PoseEstimationConfig

    @property
    def config_widget_factory(self) -> Callable[[IAppContext, PoseEstimationConfig, QWidget], IConfigWidget]:
        return PoseEstimationConfigWidget

    @property
    def pipeline_factory(self) -> Callable[[], PoseEstimationPipeline]:
        return PoseEstimationPipeline
