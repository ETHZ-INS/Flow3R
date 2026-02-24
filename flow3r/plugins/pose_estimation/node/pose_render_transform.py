from typing import Tuple, Optional

import reactivex as rx
from reactivex import operators as ops

from py3r.media.types import VideoFrame
from py3r.pose.core.types import HasPoses
from py3r.pose.core.visualization.pose_renderer import PoseRenderer

from flow3r.core.streaming.abc.transform import Transform
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


class PoseRenderTransform(Transform[Tuple[VideoFormat, PoseFormat], Tuple[VideoFrame, HasPoses], VideoFormat, VideoFrame]):
    def __init__(self):
        self._pose_renderer: Optional[PoseRenderer] = None

    def setup(self, desc_in: Tuple[VideoFormat, PoseFormat]) -> None:
        pose_format = desc_in[1]
        self._pose_renderer = PoseRenderer(pose_format.instance_types)

    def infer_descriptor(self, desc_in: Tuple[VideoFormat, PoseFormat]) -> VideoFormat:
        return desc_in[0]

    def transform_observable(self, obs: rx.Observable[Tuple[VideoFrame, HasPoses]]) -> rx.Observable[VideoFrame]:
        def _visualize(pair: Tuple[VideoFrame, HasPoses]) -> VideoFrame:
            frame, poses = pair
            try:
                vis_img = self._pose_renderer.render(frame.img, poses.instances)
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise e
            return frame.with_image(vis_img)

        return obs.pipe(
            ops.map(_visualize)
        )
