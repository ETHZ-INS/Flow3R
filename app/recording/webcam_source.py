import time
from pathlib import Path

import cv2
import rx
from rx import operators as ops
from rx.scheduler import ThreadPoolScheduler


class WebcamSource:
    def __init__(
        self,
        device_index: int = 0,
        scheduler: ThreadPoolScheduler | None = None
    ):
        self.device_index = device_index
        self.scheduler = scheduler or ThreadPoolScheduler(1)

        # internal handles
        self._connectable = None
        self._conn = None

        self.last_ts = None

        # build the (cold) Observable → publish() → connectable
        self._build_connectable()

    @property
    def stream(self) -> rx.core.Observable:
        """Observable that yields (timestamp, frame) tuples."""
        return self._connectable

    def start(self) -> None:
        """Begin the capture loop (idempotent)."""
        if self._conn is None:
            self._conn = self._connectable.connect()

    def stop(self) -> None:
        """Stop capturing and release the camera."""
        if self._conn is not None:
            self._conn.dispose()
            self._conn = None

    def _build_connectable(self) -> None:
        """Create the connectable Observable but don't connect it yet."""

        def _capture(observer, _sched):
            cap = cv2.VideoCapture(self.device_index)

            if not cap.isOpened():
                observer.on_error(RuntimeError(f"Failed to open camera device {self.device_index}"))

            try:
                while cap.isOpened():
                    ok, frame = cap.read()
                    if not ok:
                        break
                    observer.on_next((time.time(), frame))
            finally:
                cap.release()
                observer.on_completed()

        # cold → subscribe_on (capture thread) → publish (multicast)
        self._connectable = (
            rx.create(_capture)
            .pipe(
                ops.subscribe_on(self.scheduler),  # run loop on dedicated thread
                ops.publish(),                      # make it a ConnectableObservable
            )
        )
