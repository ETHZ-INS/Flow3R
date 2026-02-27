from flow3r.core.api.plugins.plugins import IPluginAPI
from flow3r.core.plugin.plugin import IPlugin
from flow3r.plugins.homecage.pipeline.homecage_analysis.pipeline_type import HomecageAnalysisPipelineType


class HomecagePlugin(IPlugin):
    def initialize(self, api: IPluginAPI):
        api.pipeline_types.register(HomecageAnalysisPipelineType())
