from typing import Optional, List

import reactivex as rx
from reactivex import operators as ops

from py3r.media.types import VideoFrame
from py3r.pose.core.model.pose_model import PoseModel
from py3r.pose.core.types import VideoFramePoses

from aaaflow3r.core.streaming.abc.transform import Transform
from aaaflow3r.plugins.core.typing.video import VideoFormat
from aaaflow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


class PoseEstimationTransform(Transform[VideoFormat, VideoFrame, PoseFormat, VideoFramePoses]):
    def __init__(self, pose_model_service, pose_model_id, batch_size: int = 1):
        self._pose_model_service = pose_model_service
        self._pose_model_id = pose_model_id
        self._batch_size = batch_size

        self._instance_types = pose_model_service.get_instance_types(pose_model_id)
        self._pose_model: Optional[PoseModel] = None

    def setup(self, desc_in: VideoFormat) -> None:
        self._pose_model = self._pose_model_service.get_pose_model(self._pose_model_id)

    def cleanup(self) -> None:
        self._pose_model = None

    def infer_descriptor(self, desc_in: VideoFormat) -> PoseFormat:
        return PoseFormat(self._instance_types)

    def transform_observable(self, obs: rx.Observable[VideoFrame]) -> rx.Observable[VideoFramePoses]:
        def _predict_batch(batch: List[VideoFrame]) -> List[VideoFramePoses]:
            try:
                poses = self._pose_model.predict_batch(batch)
                poses = [VideoFramePoses.from_pair(pair) for pair in zip(poses, batch)]
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise e
            return poses

        return obs.pipe(
            ops.buffer_with_count(self._batch_size),
            ops.map(_predict_batch),
            ops.concat_map(lambda x: rx.from_iterable(x))
        )
