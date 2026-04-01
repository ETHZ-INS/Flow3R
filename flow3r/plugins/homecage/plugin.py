from flow3r.core.api.plugins.plugins import IPluginAPI
from flow3r.core.plugin.plugin import IPlugin
from flow3r.plugins.homecage.pipeline.homecage_analysis.config import HomecageAnalysisConfig
from flow3r.plugins.homecage.pipeline.homecage_analysis.pipeline_type import HomecageAnalysisPipelineType


class HomecagePlugin(IPlugin):
    @property
    def name(self) -> str:
        return "ETH3RHub Homecage"

    def initialize(self, api: IPluginAPI):
        api.config_types.register(HomecageAnalysisConfig.TYPE_ID, HomecageAnalysisConfig)

        api.pipeline_types.register(HomecageAnalysisPipelineType())
