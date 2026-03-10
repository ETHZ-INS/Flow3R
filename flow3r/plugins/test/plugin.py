from flow3r.core.api.plugins.plugins import IPluginAPI
from flow3r.core.plugin.plugin import IPlugin
from flow3r.plugins.test.visualization.video.visualizer_type import RedVideoVisualizerType


class TestPlugin(IPlugin):
    @property
    def name(self) -> str:
        return "Test"

    def initialize(self, api: IPluginAPI):
        api.visualizer_types.register(RedVideoVisualizerType())
