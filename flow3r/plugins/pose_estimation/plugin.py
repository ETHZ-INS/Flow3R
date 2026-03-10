from flow3r.core.api.plugins.plugins import IPluginAPI
from flow3r.core.plugin.plugin import IPlugin
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.pipeline_type import MousePoseEstimationPipelineType
from flow3r.plugins.pose_estimation.pipeline.pose_estimation.pipeline_type import PoseEstimationPipelineType
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.entry import PoseEstimationModelsSettingsMenu
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelsSettings
from flow3r.plugins.pose_estimation.visualization.dynamic_pose_render.visualizer_type import DynamicPoseVisualizerType
from flow3r.plugins.pose_estimation.visualization.pose_magnifier.visualizer_type import PoseMagnifierVisualizerType
from flow3r.plugins.pose_estimation.visualization.static_pose_render.visualizer_type import StaticPoseVisualizerType


class PoseEstimationPlugin(IPlugin):
    @property
    def name(self) -> str:
        return "Pose Estimation"

    def initialize(self, api: IPluginAPI):
        api.settings.register_setting(("pose_estimation", "models"), PoseEstimationModelsSettings())
        api.settings_menus.register(PoseEstimationModelsSettingsMenu())

        api.visualizer_types.register(StaticPoseVisualizerType())
        api.visualizer_types.register(DynamicPoseVisualizerType())
        api.visualizer_types.register(PoseMagnifierVisualizerType())

        api.pipeline_types.register(PoseEstimationPipelineType())
        api.pipeline_types.register(MousePoseEstimationPipelineType())
