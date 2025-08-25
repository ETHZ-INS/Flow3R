import threading
import time
from concurrent.futures import Future
from pathlib import Path

import numpy as np
import rx
from pypylon import pylon
from rx import operators as ops
from rx.disposable import Disposable


def process_grab_result(grab_result: pylon.GrabResult) -> (bool, int, float, np.ndarray):
    if not grab_result.IsValid():
        # I think this means there is no new frame available, but it might be the other one
        grab_result.Release()
        return False, None, None, None

    if not grab_result.GrabSucceeded():
        # TODO: Is this exception worthy?
        grab_result.Release()
        return False, None, None, None

    timestamp = grab_result.GetTimeStamp()
    if timestamp == 0:
        # The emulated pylon cameras (for test purposes only) return 0 for timestamp
        timestamp = time.time()
    else:
        timestamp = timestamp / 125000000

    frame_number = grab_result.GetImageNumber()

    frame = grab_result.GetArray()

    if frame.ndim == 2:
        frame = np.broadcast_to(frame[..., None], frame.shape + (3,))
    elif frame.shape[2] == 1:
        frame = np.broadcast_to(frame, frame.shape[:2] + (3,))

    return True, frame_number, timestamp, frame


class PylonCameraSource:
    def __init__(self, device_name: str, config_file: Path | None = None):
        self._device_name = device_name
        self._config_file = config_file

        self.width = 1280
        self.height = 1024
        self.fps = 30.0

        self._probe()

        self._stream = self._build_stream()

        self.opened = False
        self.closed = Future()

    def _probe(self):
        """Probe the camera to get its properties."""
        tlf = pylon.TlFactory.GetInstance()
        devices = tlf.EnumerateDevices()
        devices = [device for device in devices if device.GetSerialNumber() == self._device_name]
        if len(devices) == 0:
            raise ValueError(f"Device with serial number '{self._device_name}' not found.")
        camera = pylon.InstantCamera(tlf.CreateDevice(devices[0]))
        camera.Open()

        try:
            print(self._device_name)
            if self._config_file is not None:
                pylon.FeaturePersistence.Load(str(self._config_file), camera.GetNodeMap(), True)
            elif self._device_name.startswith("0815-"):
                camera.Width.SetValue(1280)
                camera.Height.SetValue(1024)
                camera.AcquisitionFrameRateAbs.SetValue(30.0)

            self.width = camera.Width.GetValue()
            self.height = camera.Height.GetValue()

            if hasattr(camera, "AcquisitionFrameRateAbs"):
                print(f"AcquisitionFrameRateAbs: {camera.AcquisitionFrameRateAbs.GetValue()}")
                self.fps = camera.AcquisitionFrameRateAbs.GetValue() or 30.0
            else:
                self.fps = 30.0
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Failed to probe camera {self._device_name}: {e}")
        finally:
            camera.Close()

    def get_frame_dimensions(self) -> tuple[int, int, int]:
        return self.width, self.height, 1

    def get_fps(self) -> float:
        return self.fps

    @property
    def stream(self) -> rx.core.Observable:
        return self._stream

    def _build_stream(self) -> rx.core.Observable:
        tlf = pylon.TlFactory.GetInstance()
        devices = tlf.EnumerateDevices()
        devices = [device for device in devices if device.GetSerialNumber() == self._device_name]
        if len(devices) == 0:
            raise ValueError(f"Device with serial number '{self._device_name}' not found.")
        camera = pylon.InstantCamera(tlf.CreateDevice(devices[0]))

        def _capture(observer, _sched):
            self.opened = True
            stop = threading.Event()

            def loop():
                print(f"[PylonCameraSource] Opening Pylon Device {self._device_name}")

                camera.Open()
                try:
                    if self._config_file is not None:
                        pylon.FeaturePersistence.Load(str(self._config_file), camera.GetNodeMap(), True)
                    elif self._device_name.startswith("0815-"):
                        camera.Width.SetValue(1280)
                        camera.Height.SetValue(1024)
                        camera.AcquisitionFrameRateAbs.SetValue(30.0)

                    camera.MaxNumBuffer = 1000
                    camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

                    while not stop.is_set() and camera.IsGrabbing():
                        grab_result = camera.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException)
                        success, frame_number, timestamp, frame = process_grab_result(grab_result)
                        if success:
                            observer.on_next((frame_number, timestamp, frame))
                        grab_result.Release()
                except Exception as e:
                    observer.on_error(e)
                else:
                    observer.on_completed()
                finally:
                    camera.StopGrabbing()
                    self.closed.set_result(True)
                    print(f"[PylonCameraSource] Stopped grabbing for {self._device_name}")

            threading.Thread(target=loop, daemon=True).start()
            return Disposable(lambda: stop.set())

        return rx.create(_capture).pipe(ops.share())

    def wait(self, timeout=None):
        # TODO: maybe make thread safe?
        if self.opened:
            self.closed.result(timeout=timeout)
