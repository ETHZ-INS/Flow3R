import random
import threading
import time
from concurrent.futures import Future

import cv2
import rx
from   rx import operators as ops
from   rx.disposable import Disposable

from app.recording.camera.camera_source import CameraSource


class WebcamCameraSource(CameraSource):
    def __init__(self, device_index: int = 0):
        self._device_index = device_index

        self.width = 1920
        self.height = 1080
        self.fps = 30.0

        self._probe()

        self._stream = self._build_stream()
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
        cap = cv2.VideoCapture(self._device_index)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open camera: {self._device_index}")

        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()

    def _build_stream(self) -> rx.core.Observable:
        def _capture(observer, _):
            print(f"[WebcamCameraSource] opening camera {self._device_index}...")
            self.opened = True
            cap = cv2.VideoCapture(self._device_index)
            if not cap.isOpened():
                cap.release()
                self.closed.set_result(True)
                observer.on_error(RuntimeError(f"Camera {self._device_index} failed"))
                return Disposable()

            stop = threading.Event()
            start = None

            def loop():
                idx = 0
                try:
                    while not stop.is_set():
                        ok, frame = cap.read()
                        if not ok:
                            break
                        now = time.perf_counter()
                        nonlocal start
                        if start is None:
                            start = now
                        ts = now - start
                        observer.on_next((idx, ts, frame))
                        idx += 1
                        #if idx == 180:
                        #    raise RuntimeError("Simulated camera disconnect")
                except Exception as e:
                    observer.on_error(e)
                else:
                    observer.on_completed()
                finally:
                    cap.release()
                    self.closed.set_result(True)
                    print(f"[WebcamCameraSource] camera {self._device_index} closed")

            threading.Thread(target=loop, daemon=True).start()
            return Disposable(lambda: stop.set())

        return rx.create(_capture).pipe(ops.share())

    def is_closed(self) -> bool:
        return self.closed.done()

    def wait(self, timeout=None):
        # TODO: maybe make thread safe?
        if self.opened:
            self.closed.result(timeout=timeout)
