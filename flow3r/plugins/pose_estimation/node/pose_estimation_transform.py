import threading
import time
from typing import Optional, List, Tuple, Union

import reactivex as rx
from py3r.pose.yolo.model.staged_yolo_pose_model import StagedYoloPoseModel
from reactivex import operators as ops

from py3r.media.types import VideoFrame
from py3r.pose.core.types import VideoFramePoses, Poses

from flow3r.core.streaming.abc.transform import Transform
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelConfig
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat
from flow3r.plugins.pose_estimation.util.pose_model_service import PoseModelService, PoseModelLease


class PoseEstimationTransform(Transform[VideoFormat, VideoFrame, PoseFormat, VideoFramePoses]):
    def __init__(self, pose_model_service: PoseModelService, pose_model_config: Union[PoseEstimationModelConfig, Tuple[PoseEstimationModelConfig, ...]], batch_size: int = 1):
        self._pose_model_service = pose_model_service
        self._pose_model_config = pose_model_config
        self._batch_size = batch_size

        self._instance_types = pose_model_service.get_instance_types(pose_model_config)

        self._pose_model_lease: Optional[PoseModelLease] = None
        self._pose_model = None

        self._lock = threading.Lock()

    def setup(self, desc_in: VideoFormat) -> None:
        print(id(self), "Setup.........................")
        channels = 1 if desc_in.fmt == "mono8" else 3
        self._pose_model_lease = self._pose_model_service.get_model(self._pose_model_config)
        self._pose_model = StagedYoloPoseModel(self._pose_model_lease.model, max_batch=self._batch_size, input_channels=channels)

    def cleanup(self) -> None:
        print(threading.current_thread().name, "Cleanup.........................",)
        with self._lock:
            if self._pose_model_lease is not None:
                self._pose_model = None
                self._pose_model_lease.dispose()
                self._pose_model_lease = None
        print(threading.current_thread().name, "Cleanup.........................", "Done")

    def infer_format(self, desc_in: VideoFormat) -> PoseFormat:
        return PoseFormat(self._instance_types)

    def transform_observable(self, obs: rx.Observable[VideoFrame]) -> rx.Observable[VideoFramePoses]:
        def _predict_batch(batch: List[VideoFrame]) -> List[VideoFramePoses]:
            #print(threading.current_thread().name, "Predicting batch of size", len(batch))
            time.sleep(0.1)
            try:
                with self._lock:
                    if self._pose_model is None:
                        poses = [Poses()] * len(batch)
                        raise RuntimeError("Pose model is not available")
                    else:
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
