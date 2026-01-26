from aaaflow3r.core.visualization.abc.visualizer_type import IVisualizerType
from aaaflow3r.core.visualization.visualizer_handle import VisualizerHandle
from aaaflow3r.plugins.core.visualization.video.widget import VideoWidget


class VideoVisualizerType(IVisualizerType):
    @property
    def name(self) -> str:
        return "Video"

    @property
    def handle_factory(self):
        return VisualizerHandle

    @property
    def widget_factory(self):
        return VideoWidget
