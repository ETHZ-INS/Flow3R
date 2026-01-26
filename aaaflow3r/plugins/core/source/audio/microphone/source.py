import queue
import threading
from pathlib import Path
from typing import Optional

import numpy as np
from py3r.media.streaming.video.video_source_observable import video_source_observable
from py3r.media.types import VideoFrame
from py3r.media.video.ffmpeg_video_file_source import FFmpegVideoFileSource
import reactivex as rx
from reactivex import Subject

import sounddevice as sd

from aaaflow3r.core.source.abc.source import ISource
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.plugins.core.source.audio.microphone.config import MicrophoneSourceConfig
from aaaflow3r.plugins.core.source.video.video_file.config import VideoFileSourceConfig
from aaaflow3r.plugins.core.typing.video import VideoFormat


class MicRecorder:
    """
    Records mono audio chunks from an input device and exposes them as an Rx Observable[np.ndarray].

    Emitted chunks:
      - shape: (frames,)
      - dtype: float32
      - range: approx [-1, 1]
    """

    def __init__(
        self,
        *,
        sample_rate: int = 48_000,
        chunk_frames: int = 1024,
        device: Optional[int] = None,  # sounddevice device index; None = default input
        max_queue_chunks: int = 32,
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_frames = chunk_frames
        self.device = device

        self._subject: Subject = Subject()
        self.observable: rx.Observable = self._subject  # public

        self._q: queue.Queue[np.ndarray] = queue.Queue(maxsize=max_queue_chunks)
        self._stop_evt = threading.Event()
        self._pump_thread: Optional[threading.Thread] = None
        self._stream: Optional[sd.InputStream] = None

    @staticmethod
    def list_input_devices() -> list[dict]:
        """Utility to help you find the USB mic index."""
        devices = sd.query_devices()
        out = []
        for idx, d in enumerate(devices):
            if d.get("max_input_channels", 0) > 0:
                out.append({"index": idx, "name": d.get("name"), "max_input_channels": d.get("max_input_channels")})
        return out

    def start(self) -> None:
        if self._stream is not None:
            return

        self._stop_evt.clear()

        def callback(indata: np.ndarray, frames: int, time, status) -> None:
            # indata shape is (frames, channels). We request channels=1 and dtype=float32.
            if status:
                # Don't spam; you can route to logging if you want.
                pass

            # Convert to 1D contiguous mono float32
            chunk = np.ascontiguousarray(indata[:, 0], dtype=np.float32)

            # Latest-only-ish behavior at the source: if queue is full, drop older chunks
            # so UI doesn't lag behind.
            try:
                self._q.put_nowait(chunk)
            except queue.Full:
                try:
                    _ = self._q.get_nowait()  # drop one
                except queue.Empty:
                    pass
                try:
                    self._q.put_nowait(chunk)
                except queue.Full:
                    pass

        # Pump thread: emits chunks from the callback queue into the Rx Subject.
        # (Keeps callback fast and avoids emitting from the PortAudio callback thread.)
        def pump() -> None:
            try:
                while not self._stop_evt.is_set():
                    try:
                        chunk = self._q.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    self._subject.on_next(chunk)
            except Exception as e:
                self._subject.on_error(e)

        self._pump_thread = threading.Thread(target=pump, daemon=True)
        self._pump_thread.start()

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.chunk_frames,
            device=self.device,
            channels=1,          # mono
            dtype="float32",     # emits float32 in [-1,1]
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is None:
            return

        self._stop_evt.set()

        try:
            self._stream.stop()
            self._stream.close()
        finally:
            self._stream = None

        # Finish the observable
        self._subject.on_completed()


class MicrophoneSource(ISource[VideoFrame]):
    def __init__(self, config: MicrophoneSourceConfig):
        self._recorder = MicRecorder(device=config.device_index)
        self._desc_subject = Subject()
        self._frame_observable = self._recorder.observable
        self._stream = Stream(self._desc_subject, self._frame_observable)

    @property
    def stream(self) -> Stream[VideoFrame]:
        return self._stream

    def open(self):
        self._recorder.start()
        self._desc_subject.on_next(None)

    def close(self):
        self._recorder.stop()
        self._desc_subject.on_completed()
