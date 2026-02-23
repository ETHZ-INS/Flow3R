from aaaflow3r.core.api.plugins.plugins import IPluginAPI
from aaaflow3r.core.plugin.plugin import IPlugin
from aaaflow3r.plugins.test.visualization.video.visualizer_type import RedVideoVisualizerType


class TestPlugin(IPlugin):
    def initialize(self, api: IPluginAPI):
        api.visualizer_types.register(RedVideoVisualizerType())
