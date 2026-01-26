from aaaflow3r.core.api.plugins import IPluginAPI
from aaaflow3r.core.plugin.plugin import IPlugin
from aaaflow3r.plugins.test.pipeline.test.pipeline_type import TestPipelineType


class TestPlugin(IPlugin):
    def initialize(self, api: IPluginAPI):
        api.source_types.register(VideoTestSourceType())
        api.pipeline_types.register(TestPipelineType())
