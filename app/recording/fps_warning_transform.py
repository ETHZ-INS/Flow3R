import time, rx
from   rx import operators as ops
from   typing import List, Any

class FPSWarningTransform:
    def __init__(self, window: int = 30, target_fps: float = 30.0):
        self._win: List[float | None] = [None] * window
        self._size  = window
        self._target_fps = target_fps
        self._count = 0
        self._idx   = 0

    # ----------------------------------------------------------------
    def _update(self, item: Any) -> float:
        current_index = self._idx

        self._win[self._idx] = time.perf_counter()
        self._idx = (self._idx + 1) % self._size
        self._count = min(self._count + 1, self._size)

        oldest_index = (self._idx - self._count) % self._size
        oldest = self._win[oldest_index]
        now = self._win[current_index]

        if self._count > 1:
            dt = now - oldest  # time covering (count-1) frames
            fps = (self._count - 1) / max(dt, 1e-6)

            if fps < self._target_fps * 0.95:
                print(self._count, f"Warning: FPS dropped below target ({fps:.2f} < {self._target_fps:.2f})")

        return item

    # ----------------------------------------------------------------
    def __call__(self, upstream: rx.Observable) -> rx.Observable:
        return upstream.pipe(
            ops.map(self._update),
            ops.finally_action(self._reset)
        )

    def _reset(self):
        self._win[:] = [None] * self._size
        self._count  = 0
        self._idx    = 0
