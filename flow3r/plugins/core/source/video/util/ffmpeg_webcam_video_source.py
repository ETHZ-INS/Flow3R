import re
import subprocess
import time
from typing import Optional, Tuple, List

import numpy as np

from py3r.media.types import VideoFrame
from py3r.media.video import VideoSource


class FFmpegWebcamSource(VideoSource):
    ffmpeg_executable = "ffmpeg"

    def __init__(
        self,
        device_name: Optional[str] = None,
        device_index: Optional[int] = None,
        grayscale: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[float] = None,
        loglevel: str = "error",
    ):
        """
        Windows / DirectShow webcam source via ffmpeg.

        Use either:
            - device_name="Integrated Camera"
        or:
            - device_index=0

        Note:
            device_index here is YOUR convenience index based on the order returned
            by `ffmpeg -list_devices true -f dshow -i dummy`, not a native dshow API.
        """
        if device_name is None and device_index is None:
            device_index = 0
        if device_name is not None and device_index is not None:
            raise ValueError("Specify either device_name or device_index, not both.")

        self._device_name = device_name
        self._device_index = device_index
        self._device_number = 0  # for duplicate names in dshow output

        self._grayscale = grayscale
        self._requested_width = width
        self._requested_height = height
        self._requested_fps = fps
        self._loglevel = loglevel

        self._proc: Optional[subprocess.Popen] = None

        self._idx = 0
        self._size: Optional[Tuple[int, int]] = None
        self._fps: Optional[float] = fps
        self._channels = 1 if grayscale else 3

        self._frame_nbytes = 0
        self._frame_bytes: Optional[bytearray] = None
        self._mv = None

        self._resolve_device()
        self._probe()

    # ---------- Public API ----------
    def open(self) -> None:
        self._start_proc()
        self._idx = 0

    def close(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()
        self._proc = None

    def is_open(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def has_timing(self) -> bool: return True
    def has_size(self) -> bool: return self._size is not None
    def has_fps(self) -> bool: return self._fps is not None
    def has_num_frames(self) -> bool: return False
    def is_seekable(self) -> bool: return False

    def get_size(self) -> Optional[Tuple[int, int]]: return self._size
    def get_fps(self) -> Optional[float]: return self._fps
    def get_num_channels(self) -> int: return self._channels
    def get_num_frames(self) -> Optional[int]: return None

    def seek(self, frame_index: int) -> None:
        # live source; no-op
        pass

    def read(self, timeout: Optional[float] = None) -> Optional[VideoFrame]:
        arr = self._try_read(timeout)
        if arr is None:
            return None

        w, h = self._size
        if self._channels == 1:
            img = arr.reshape((h, w))
        else:
            img = arr.reshape((h, w, 3))  # BGR

        ts = time.perf_counter()
        frame = VideoFrame(img, self._idx, ts)
        self._idx += 1
        return frame

    # ---------- Device enumeration helpers ----------
    @classmethod
    def list_video_devices(cls) -> List[str]:
        """
        Returns video device names in the order ffmpeg lists them.

        Duplicate names are returned multiple times.
        """
        cmd = [
            str(cls.ffmpeg_executable),
            "-hide_banner",
            "-list_devices", "true",
            "-f", "dshow",
            "-i", "dummy",
        ]

        # ffmpeg prints device list to stderr and usually exits non-zero here.
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        text = proc.stderr
        devices = []

        for line in text.splitlines():
            if not line.endswith("(video)"):
                continue

            m = re.search(r'"([^"]+)"', line)
            if m:
                devices.append(m.group(1))

        return devices

    @classmethod
    def list_video_device_entries(cls) -> List[Tuple[int, str, int]]:
        """
        Returns [(global_index, device_name, video_device_number), ...].

        video_device_number is the dshow duplicate-name selector.
        """
        names = cls.list_video_devices()
        counts = {}
        out = []
        for i, name in enumerate(names):
            n = counts.get(name, 0)
            out.append((i, name, n))
            counts[name] = n + 1
        return out

    def _resolve_device(self) -> None:
        if self._device_name is not None:
            self._device_number = 0
            return

        entries = self.list_video_device_entries()
        if not entries:
            raise RuntimeError("No DirectShow video devices found")

        idx = int(self._device_index)
        if idx < 0 or idx >= len(entries):
            raise IndexError(
                f"device_index {idx} out of range; found {len(entries)} video device(s)"
            )

        _, name, devnum = entries[idx]
        self._device_name = name
        self._device_number = devnum

    # ---------- Probe ----------
    def _probe(self) -> None:
        """
        For ffmpeg+dshow, probing is much weaker than ffprobe on a file.
        Best approach:
          - if width/height were requested, trust them
          - otherwise try to infer one usable mode from `-list_options true`
          - fps is set from requested_fps if given, otherwise left None
        """
        if self._requested_width is not None and self._requested_height is not None:
            self._size = (self._requested_width, self._requested_height)
            self._fps = self._requested_fps
            self._allocate_frame_buffer()
            return

        size = self._probe_first_video_size()
        self._size = size
        self._fps = self._requested_fps
        if self._size is not None:
            self._allocate_frame_buffer()

    def _probe_first_video_size(self) -> Optional[Tuple[int, int]]:
        cmd = [
            str(self.ffmpeg_executable),
            "-hide_banner",
            "-list_options", "true",
            "-f", "dshow",
            "-i", f'video={self._device_name}',
        ]
        if self._device_number:
            cmd[1:1] = ["-video_device_number", str(self._device_number)]

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        text = proc.stderr

        # Match things like:
        #   min s=640x480 fps=5 max s=640x480 fps=30
        #   or
        #   vcodec=mjpeg  min s=1280x720 fps=30 max s=1280x720 fps=30
        matches = re.findall(r"s=(\d+)x(\d+)", text)
        if not matches:
            return None

        # Pick first advertised size; simple and usually good enough.
        w, h = matches[0]
        return int(w), int(h)

    def _allocate_frame_buffer(self) -> None:
        w, h = self._size
        self._frame_nbytes = w * h * self._channels
        self._frame_bytes = bytearray(self._frame_nbytes)
        self._mv = memoryview(self._frame_bytes)

    # ---------- Reading ----------
    def _start_proc(self) -> None:
        if self._size is None:
            raise RuntimeError(
                "Camera size is unknown. Pass width=... and height=..., "
                "or improve probing for your device."
            )

        self._allocate_frame_buffer()

        pix_fmt = "gray" if self._grayscale else "bgr24"

        cmd = [
            str(self.ffmpeg_executable),
            "-hide_banner",
            "-loglevel", self._loglevel,
            "-nostdin",
            "-f", "dshow",
        ]

        if self._requested_fps is not None:
            cmd += ["-framerate", str(self._requested_fps)]

        if self._requested_width is not None and self._requested_height is not None:
            cmd += ["-video_size", f"{self._requested_width}x{self._requested_height}"]

        if self._device_number:
            cmd += ["-video_device_number", str(self._device_number)]

        cmd += [
            "-i", f'video={self._device_name}',
            "-an", "-sn", "-dn",
            "-pix_fmt", pix_fmt,
            "-f", "rawvideo",
            "pipe:1",
        ]

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

    def _try_read(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
        if not self.is_open():
            return None

        stdout = self._proc.stdout
        if stdout is None:
            return None

        ok = self._read_exact_into(stdout, timeout=timeout)
        if not ok:
            return None

        return np.frombuffer(
            self._frame_bytes,
            dtype=np.uint8,
            count=self._frame_nbytes
        ).copy()

    def _read_exact_into(self, stdout, timeout: Optional[float]) -> bool:
        remaining = self._frame_nbytes
        offset = 0
        start = time.perf_counter()

        while remaining > 0:
            n = stdout.readinto(self._mv[offset:offset + remaining])
            if not n:
                return False
            remaining -= n
            offset += n

            if timeout is not None and (time.perf_counter() - start) > timeout:
                raise TimeoutError("Timeout reading frame")

        return True
