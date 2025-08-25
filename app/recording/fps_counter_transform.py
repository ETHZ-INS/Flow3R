import time, rx
from   rx import operators as ops
from   typing import List, Any

class FPSCounterTransform:
    """Emit the current FPS, using a sliding-window of the last *N* frames."""

    def __init__(self, window: int = 30):
        self._win: List[float | None] = [None] * window
        self._size  = window
        self._count = 0
        self._idx   = 0

    # ----------------------------------------------------------------
    def _update(self, _unused: Any) -> float:
        now = time.perf_counter()

        self._win[self._idx] = now
        self._idx = (self._idx + 1) % self._size
        self._count = min(self._count + 1, self._size)

        if self._count <= 1:
            return 0.0

        oldest = self._win[(self._idx - self._count) % self._size]
        dt = now - oldest  # time covering (count-1) frames
        fps = (self._count - 1) / max(dt, 1e-6)

        return fps

    # ----------------------------------------------------------------
    def __call__(self, upstream: rx.Observable) -> rx.Observable:
        return upstream.pipe(
            ops.map(self._update),               # replace item with FPS
            ops.finally_action(self._reset)
        )

    def _reset(self):
        self._win[:] = [None] * self._size
        self._count  = 0
        self._idx    = 0
