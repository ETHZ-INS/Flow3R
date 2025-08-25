from typing import Tuple

import numpy as np
import rx
from rx import operators as ops

class RelativeTimeTransform:
    def __init__(self):
        self._first_timestamp = None
        self._frame_index = 0

    def reset(self):
        self._first_timestamp = None
        self._frame_index = 0

    def _get_timestamp(self, frame: Tuple[int, float, np.ndarray]) -> Tuple[int, float, np.ndarray]:
        fn, timestamp, frame = frame
        if self._first_timestamp is None:
            self._first_timestamp = timestamp
        timestamp -= self._first_timestamp
        fn = self._frame_index
        self._frame_index += 1
        return fn, timestamp, frame

    def __call__(self, upstream: rx.Observable) -> rx.Observable:
        return upstream.pipe(
            ops.map(self._get_timestamp),
            ops.finally_action(self.reset)
        )