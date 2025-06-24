import time
from pathlib import Path

import cv2
import rx
from rx import operators as ops
from rx.scheduler import ThreadPoolScheduler


class VideoFileCameraSource:
    def __init__(
        self,
        video_file: Path,
        scheduler: ThreadPoolScheduler | None = None,
    ):
        self.video_file = video_file
        self.scheduler = scheduler or ThreadPoolScheduler(1)

        # internal handles
        self._connectable = None
        self._conn = None

        self.first_timestamp = None
        self.frame_index = 0

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
            cap = cv2.VideoCapture(str(self.video_file))

            if not cap.isOpened():
                observer.on_error(RuntimeError(f"Failed to open video file: {self.video_file}"))

            try:
                while cap.isOpened():
                    ok, frame = cap.read()
                    if not ok:
                        break
                    timestamp = time.time()
                    if self.first_timestamp is None:
                        self.first_timestamp = timestamp
                    timestamp -= self.first_timestamp  # normalize to start time
                    observer.on_next((self.frame_index, timestamp, frame))
                    self.frame_index += 1
                    time.sleep(1/30)  # simulate ~30 FPS
            except Exception as e:
                # Print stack trace for debugging
                observer.on_error(e)
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
