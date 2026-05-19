from typing import Any

from flow3r.core.visualization.abc.visualizer_type import IVisualizerType
from flow3r.core.visualization.visualizer_handle import VisualizerHandle
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat
from flow3r.plugins.pose_estimation.visualization.static_pose_render.widget import StaticPoseWidget


class StaticPoseVisualizerType(IVisualizerType):
    @property
    def name(self) -> str:
        return "Render Pose (Static)"

    @property
    def handle_factory(self):
        return VisualizerHandle

    @property
    def widget_factory(self):
        return StaticPoseWidget

    def accepts(self, desc: Any) -> bool:
        return isinstance(desc, tuple) and isinstance(desc[0], VideoFormat) and isinstance(desc[1], PoseFormat)