from aaaflow3r.core.api.plugins.plugins import IPluginAPI
from aaaflow3r.core.plugin.plugin import IPlugin
from aaaflow3r.plugins.pose_estimation.pipeline.pose_estimation.pipeline_type import PoseEstimationPipelineType


class PoseEstimationPlugin(IPlugin):
    def initialize(self, api: IPluginAPI):
        api.pipeline_types.register(PoseEstimationPipelineType())
