from pathlib import Path
from concurrent.futures import Future, CancelledError
from threading import Lock
import cv2
import numpy as np

from rx import operators as ops
from rx.core import Observer
from rx.scheduler import ThreadPoolScheduler


class VideoFileSink(Observer):
    """
    An RxPY Observer that writes frames to a video file.

    - Exposes a single Future: `result`
        * result.set_result(Path) on success
        * result.set_exception(exc) on failure
        * result.set_exception(CancelledError()) on cancel/dispose before completion
    - Thread-safe and idempotent teardown.
    - Guards against late on_next/on_error/on_completed after dispose().
    """
    def __init__(
        self,
        video_file: Path,
        width: int = 1280,
        height: int = 1024,
        fps: float = 30.0,
        codec: str = "mp4v",
        scheduler=None,
    ):
        super().__init__()
        self._video_file = Path(video_file)
        self._worker = scheduler or ThreadPoolScheduler(1)

        self._width = width
        self._height = height

        self._vw = cv2.VideoWriter(
            str(self._video_file),
            cv2.VideoWriter.fourcc(*codec),
            fps,
            (width, height),
        )

        self.result: Future[Path] = Future()

        self._sub = None
        self._stopped = False
        self._lock = Lock()

    # ---------- Observer interface ----------
    def on_next(self, frame):
        # Fast no-op if we already stopped or writer is gone.
        if self._stopped or self._vw is None:
            return

        try:
            write_frame = frame[2]
            assert isinstance(write_frame, np.ndarray)

            if write_frame.shape != (self._height, self._width, 3):
                raise ValueError(f"Frame shape {write_frame.shape} does not match expected ({self._height}, {self._width}, 3)")

            if not self._vw.isOpened():
                raise RuntimeError("VideoWriter is not opened")
            self._vw.write(write_frame)
        except Exception as e:
            print(f"[VideoFileSink] error: {e}")
            self._fail(e)

    def on_error(self, err):
        if self._stopped:
            return
        self._fail(err)

    def on_completed(self):
        if self._stopped:
            return
        self._succeed()

    # ---------- Wiring helpers ----------
    def attach(self, upstream):
        """
        Subscribe to an Observable and remember the disposable.
        All observer callbacks are delivered on `self._worker` (serialized).
        """
        self._sub = upstream.pipe(
            ops.observe_on(self._worker),
        ).subscribe(self)
        return self._sub

    def dispose(self):
        """
        Stop receiving, release resources, and mark the result as cancelled
        if it hasn't already completed with success/exception.
        """
        self._unsubscribe()
        self._cleanup_once()
        with self._lock:
            if not self.result.done():
                self.result.set_exception(CancelledError("VideoFileSink disposed"))

    # ---------- Internals ----------
    def _unsubscribe(self):
        sub = self._sub
        self._sub = None
        if sub is not None:
            try:
                sub.dispose()
            except Exception:
                pass  # best effort

    def _cleanup_once(self):
        with self._lock:
            if self._stopped:
                return
            self._stopped = True
            if self._vw is not None:
                try:
                    self._vw.release()
                finally:
                    self._vw = None

    def _fail(self, exc: Exception):
        # Ensure we stop producing and free resources first.
        self._unsubscribe()
        self._cleanup_once()
        with self._lock:
            if not self.result.done():
                self.result.set_exception(exc)

    def _succeed(self):
        # Normal completion path.
        self._unsubscribe()
        self._cleanup_once()
        with self._lock:
            if not self.result.done():
                self.result.set_result(self._video_file)
