import reactivex as rx
from py3r.pose.core.filtering.pose_filter import PoseFilter
from reactivex import operators as ops

from py3r.media.types import VideoFrame
from py3r.pose.core.types import VideoFramePoses, Poses

from flow3r.core.streaming.abc.transform import Transform
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


class PoseFilterTransform(Transform[PoseFormat, VideoFramePoses, PoseFormat, VideoFramePoses]):
    def __init__(self, pose_filter: PoseFilter):
        self._pose_filter = pose_filter

    def setup(self, desc_in: VideoFormat) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def infer_format(self, desc_in: VideoFormat) -> VideoFormat:
        return desc_in

    def transform_observable(self, obs: rx.Observable[VideoFrame]) -> rx.Observable[VideoFramePoses]:
        def _filter_poses(poses: VideoFramePoses) -> VideoFramePoses:
            filtered_poses = self._pose_filter.filter(poses)
            return poses.with_poses(filtered_poses)

        return obs.pipe(
            ops.map(_filter_poses),
        )
