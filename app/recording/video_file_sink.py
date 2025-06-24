from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
import rx
from rx.core import Observer


# TODO: Configurable size, codec, and frame rate


class VideoFileSink(Observer):
    def __init__(self, video_file: Path):
        super().__init__()
        self.video_file = video_file
        self._subscription = None

        self.vw = cv2.VideoWriter(
            str(video_file),
            cv2.VideoWriter.fourcc(*'mp4v'),  # Codec for MP4
            30.0,  # Frame rate
            (1280, 1024)  # Frame size
        )

    # ---------- Observer interface ---------------------------------
    def on_next(self, frame: Tuple[int, float, np.ndarray]):
        self.vw.write(frame[2])

    def on_error(self, err):
        print(f"[VideoFileSink] error: {err}")
        import traceback
        traceback.print_exc()
        self._cleanup()

    def on_completed(self):
        print("[VideoFileSink] completed")
        self._cleanup()

    # ---------- Convenience helpers --------------------------------
    def attach(self, upstream: rx.Observable):
        """Subscribe to an Observable and remember the disposable."""
        self._subscription = upstream.subscribe(self)
        return self._subscription

    def dispose(self):
        if self._subscription:
            self._subscription.dispose()
            self._subscription = None
        self._cleanup()

    def _cleanup(self):
        self.vw.release()
