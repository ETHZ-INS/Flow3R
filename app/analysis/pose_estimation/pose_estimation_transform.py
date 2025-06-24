import numpy as np
import rx
import rx.operators as ops
from rx.scheduler import ThreadPoolScheduler

from app.analysis.pose_estimation.pose_model import PoseModel


def ensure_3_channel_input(batch):
    """Ensure that each frame in the batch has 3 channels (RGB)."""
    return [f if f.shape[2] == 3 else np.repeat(f, 3, axis=2) for _, _, f in batch]


class PoseEstimationTransform:
    """Callable object: upstream Observable -> downstream Observable."""
    def __init__(self, model: PoseModel, batch_size: 1):
        self.model = model
        self.batch_size = batch_size
        self.scheduler = ThreadPoolScheduler(1)

    # --------------------------------------------------------------
    def _infer_batch(self, batch):
        poses = self.model.predict_frames(batch)     # heavy call
        return poses

    def __call__(self, upstream: rx.Observable) -> rx.Observable:
        return upstream.pipe(
            # 1️⃣ collect successive frames into fixed-size lists
            ops.buffer_with_count(self.batch_size),

            # 2️⃣ hop to the worker thread — every *next* operator runs there
            ops.observe_on(self.scheduler),

            # 3️⃣ ensure that each frame has 3 channels (RGB)
            ops.map(ensure_3_channel_input),          # → list[frame] with 3 channels

            # 3️⃣ run a single inference per batch
            ops.map(self._infer_batch),          # → list[(ts, pose)]

            # 4️⃣ flatten the list back into individual items
            ops.flat_map(rx.from_iterable)       # → (ts, pose) per frame
        )