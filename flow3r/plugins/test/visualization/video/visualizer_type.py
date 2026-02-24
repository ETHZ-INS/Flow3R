from typing import Any

from flow3r.core.visualization.abc.visualizer_type import IVisualizerType
from flow3r.core.visualization.visualizer_handle import VisualizerHandle
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.test.visualization.video.widget import RedVideoWidget


class RedVideoVisualizerType(IVisualizerType):
    @property
    def name(self) -> str:
        return "Red Video"

    @property
    def handle_factory(self):
        return VisualizerHandle

    @property
    def widget_factory(self):
        return RedVideoWidget

    def accepts(self, desc: Any) -> bool:
        return isinstance(desc, VideoFormat)
