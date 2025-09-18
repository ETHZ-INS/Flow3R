import random
import threading
import time
from concurrent.futures import Future
from pathlib import Path
import cv2
import rx
from   rx import operators as ops
from   rx.disposable import Disposable


class VideoFileCameraSource:
    def __init__(self, video_file: Path):
        self._video_file = Path(video_file)

        self.width = 1920
        self.height = 1080
        self.fps = 30.0

        self._probe()  # probe the video file to get its properties

        self._stream    = self._build_stream()      # build once

        self.opened = False
        self.closed = Future()

    def get_frame_dimensions(self) -> tuple[int, int, int]:
        return self.width, self.height, 3

    def get_fps(self) -> float:
        return self.fps

    @property
    def stream(self) -> rx.core.Observable:
        return self._stream

    def _probe(self):
        """Probe the video file to get its properties."""
        cap = cv2.VideoCapture(str(self._video_file))
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open: {self._video_file}")

        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()

    def _build_stream(self) -> rx.core.Observable:
        def _capture(observer, _):
            print(f"[VideoFileCameraSource] opening {self._video_file}...")
            self.opened = True
            #if random.random() < 0.5:
            #    observer.on_error(RuntimeError(f"Bad luck opening {self._video_file}"))
            cap = cv2.VideoCapture(str(self._video_file))
            if not cap.isOpened():
                self.closed.set_result(True)
                observer.on_error(RuntimeError(f"Cannot open {self._video_file}"))
                return Disposable()             # no clean-up needed

            period = 1.0 / self.fps if self.fps > 0 else 1.0 / 30.0

            stop = threading.Event()

            def loop():
                idx = 0
                t0 = time.perf_counter()
                try:
                    while not stop.is_set() and cap.isOpened():
                        #if idx == 300:
                        #    raise RuntimeError("Simulated camera disconnect")
                        ok, frame = cap.read()
                        if not ok:
                            if idx == 0:
                                observer.on_error(RuntimeError(f"Cannot read frames from {self._video_file}"))
                            else:
                                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                ok, frame = cap.read()
                            if not ok:
                                observer.on_error(RuntimeError(f"Cannot read frames from {self._video_file}"))
                                break

                        ts = idx * period
                        observer.on_next((idx, ts, frame))
                        idx += 1

                        # pace playback
                        next_t   = t0 + idx * period
                        delay    = next_t - time.perf_counter()
                        if delay > 0:
                            time.sleep(delay)
                except Exception as e:
                    observer.on_error(e)
                else:
                    observer.on_completed()
                finally:
                    cap.release()
                    self.closed.set_result(True)
                    print(f"[VideoFileCameraSource] {self._video_file} closed")

            threading.Thread(target=loop, daemon=True).start()
            return Disposable(lambda: stop.set())

        return rx.create(_capture).pipe(ops.share())

    def wait(self, timeout=None):
        # TODO: maybe make thread safe?
        if self.opened:
            self.closed.result(timeout=timeout)
