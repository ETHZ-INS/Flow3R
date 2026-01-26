from aaaflow3r.core.visualization.abc.visualizer_type import IVisualizerType
from aaaflow3r.core.visualization.visualizer_handle import VisualizerHandle
from aaaflow3r.plugins.core.visualization.audio.widget import AudioWidget


class AudioVisualizerType(IVisualizerType):
    @property
    def name(self) -> str:
        return "Audio"

    @property
    def handle_factory(self):
        return VisualizerHandle

    @property
    def widget_factory(self):
        return AudioWidget
