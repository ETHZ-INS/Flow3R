from aaaflow3r.core.api.plugins.plugins import IPluginAPI
from aaaflow3r.core.plugin.plugin import IPlugin
from aaaflow3r.plugins.pose_estimation.pipeline.pose_estimation.pipeline_type import PoseEstimationPipelineType
from aaaflow3r.plugins.pose_estimation.settings.pose_estimation_models.entry import PoseEstimationModelsSettingsMenu
from aaaflow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelsSettings
from aaaflow3r.plugins.pose_estimation.visualization.pose_render.visualizer_type import PoseVisualizerType


class PoseEstimationPlugin(IPlugin):
    def initialize(self, api: IPluginAPI):
        api.settings.register_setting(("pose_estimation", "models"), PoseEstimationModelsSettings())
        api.settings_menus.register(PoseEstimationModelsSettingsMenu())

        api.visualizer_types.register(PoseVisualizerType())

        api.pipeline_types.register(PoseEstimationPipelineType())
