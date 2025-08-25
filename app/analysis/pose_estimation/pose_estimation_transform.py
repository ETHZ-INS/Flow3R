import numpy as np
import rx
import rx.operators as ops
from py3r.point_tracking.core.data.frame import Frame
from rx.scheduler import ThreadPoolScheduler

from app.analysis.pose_estimation.pose_model import PoseModel


def ensure_3_channel_input(img):
    fn, ts, f = img
    # grayscale, plain 2-D
    if f.ndim == 2:
        v = np.broadcast_to(f[..., None], f.shape + (3,))
    # grayscale, already (H,W,1)
    elif f.shape[2] == 1:
        v = np.broadcast_to(f, f.shape[:2] + (3,))
    # already RGB/BGR
    else:
        v = f
    return fn, ts, v


class PoseEstimationTransform:
    """Callable object: upstream Observable -> downstream Observable."""
    def __init__(self, model: PoseModel, batch_size: 1):
        self.model = model
        self.batch_size = batch_size
        self.scheduler = ThreadPoolScheduler(1)

    # --------------------------------------------------------------
    def _infer_batch(self, batch):
        poses = self.model.predict_frames([f for _, _, f in batch])
        results = [Frame(fn, f.shape[1], f.shape[0], instances) for (fn, _, f), instances in zip(batch, poses)]
        return results

    def __call__(self, upstream: rx.Observable) -> rx.Observable:
        return upstream.pipe(
            ops.observe_on(self.scheduler),
            ops.map(ensure_3_channel_input),
            ops.buffer_with_count(self.batch_size),
            ops.map(self._infer_batch),
            ops.flat_map(rx.from_iterable)
        )
