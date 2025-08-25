import threading
import time
from collections.abc import Callable
from typing import Any

from rx import Observable, operators as ops


class TimedActionTransform:
    """A transform that executes an action after a specified duration. Useful for stopping the recording after a configured time."""

    def __init__(self, duration: float, action: Callable):
        self._duration = duration
        self._start_time = None
        self._action = action
        self._fired = False

    def reset(self):
        self._start_time = None

    def _update(self, item: Any):
        now = time.perf_counter()
        if self._start_time is None:
            self._start_time = now

        elapsed = now - self._start_time
        if not self._fired and elapsed >= self._duration:
            self._fired = True
            self._action()
        return item

    def __call__(self, upstream: Observable):
        return upstream.pipe(
            ops.map(self._update),
            ops.finally_action(self.reset)
        )
