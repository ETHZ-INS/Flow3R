import time
from pathlib import Path

import cv2
import numpy as np
import rx
from pypylon import pylon
from rx import operators as ops
from rx.scheduler import ThreadPoolScheduler


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
    if len(frame.shape) == 2:
        frame = frame[:, :, np.newaxis]

    return True, frame_number, timestamp, frame


class PylonCameraSource:
    def __init__(
        self,
        device_name: str,
        config_file: Path | None = None,
        scheduler: ThreadPoolScheduler | None = None
    ):
        self.device_name = device_name
        self.config_file = config_file
        self.scheduler = scheduler or ThreadPoolScheduler(1)

        # internal handles
        self._connectable = None
        self._conn = None

        self.last_system_ts = None
        self.last_camera_ts = None

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

        tlf = pylon.TlFactory.GetInstance()
        devices = tlf.EnumerateDevices()
        devices = [device for device in devices if device.GetSerialNumber() == self.device_name]
        if len(devices) == 0:
            raise ValueError(f"Device with serial number '{self.device_name}' not found.")
        camera = pylon.InstantCamera(tlf.CreateDevice(devices[0]))

        camera.Open()

        if self.config_file is not None:
            pylon.FeaturePersistence.Load(str(self.config_file), camera.GetNodeMap(), True)

        camera.MaxNumBuffer = 1000

        def _capture(observer, _sched):
            try:
                camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
                while camera.IsGrabbing():
                    last_system_ts = self.last_system_ts
                    last_camera_ts = self.last_camera_ts

                    grab_result = camera.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException)
                    self.last_system_ts = time.time()

                    success, frame_number, timestamp, frame = process_grab_result(grab_result)
                    self.last_camera_ts = timestamp

                    if last_system_ts is not None and last_camera_ts is not None:
                        print(f"{self.last_system_ts - last_system_ts:.3f}, {self.last_camera_ts - last_camera_ts:.3f}, {frame_number}")

                    observer.on_next((timestamp, frame))
            finally:
                camera.StopGrabbing()
                camera.Close()
                observer.on_completed()

        # cold → subscribe_on (capture thread) → publish (multicast)
        self._connectable = (
            rx.create(_capture)
            .pipe(
                ops.subscribe_on(self.scheduler),  # run loop on dedicated thread
                ops.publish(),                      # make it a ConnectableObservable
            )
        )
