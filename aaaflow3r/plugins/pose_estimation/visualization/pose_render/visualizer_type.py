from typing import Any

from aaaflow3r.core.visualization.abc.visualizer_type import IVisualizerType
from aaaflow3r.core.visualization.visualizer_handle import VisualizerHandle
from aaaflow3r.plugins.core.typing.video import VideoFormat
from aaaflow3r.plugins.pose_estimation.typing.pose_format import PoseFormat
from aaaflow3r.plugins.pose_estimation.visualization.pose_render.widget import PoseWidget


class PoseVisualizerType(IVisualizerType):
    @property
    def name(self) -> str:
        return "Pose"

    @property
    def handle_factory(self):
        return VisualizerHandle

    @property
    def widget_factory(self):
        return PoseWidget

    def accepts(self, desc: Any) -> bool:
        return isinstance(desc, tuple) and isinstance(desc[0], VideoFormat) and isinstance(desc[1], PoseFormat)