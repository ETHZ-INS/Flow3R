from __future__ import annotations

import queue
from dataclasses import dataclass

import sounddevice as sd

from flow3r.plugins.core.typing.audio import AudioChunk


@dataclass
class SoundDeviceMicrophoneSource:
    def __init__(self,
        samplerate: int = 48_000,
        chunk_size: int = 1600,      # samples per chunk
        channels: int = 1,
        dtype: str = "float32",
        device: int | None = None,
        max_queue_chunks: int = 0,
    ):
        self.samplerate = samplerate
        self.chunk_size = chunk_size
        self.channels = channels
        self.dtype = dtype
        self.device = device
        self.max_queue_chunks = max_queue_chunks

        self._stream: sd.InputStream | None = None
        self._q = queue.Queue(maxsize=self.max_queue_chunks)

    def open(self) -> None:
        def callback(indata, _frames, time, status):
            # indata: shape (frames, channels)
            # time.inputBufferAdcTime: timestamp (seconds) of the first sample in this block
            # status: overflow/underflow indicators
            if status:
                # You can log status if useful; avoid heavy work in callback.
                pass

            # Copy because PortAudio reuses the input buffer memory
            samples = indata.copy()

            # Ensure shape (frames, channels)
            if samples.ndim == 1:
                samples = samples[:, None]

            chunk = AudioChunk(
                timestamp=float(time.inputBufferAdcTime),
                samples=samples,
            )

            try:
                self._q.put_nowait(chunk)
            except queue.Full:
                # Consumer is too slow. Drop newest or oldest; here we drop newest.
                # Alternative: clear queue then put latest to keep "most recent" audio.
                pass

        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            blocksize=self.chunk_size,
            channels=self.channels,
            dtype=self.dtype,
            device=self.device,
            callback=callback,
        )
        self._stream.start()

    def close(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
            finally:
                self._stream.close()
        self._stream = None

        # Unblock any waiting read()
        if self._q is not None:
            try:
                self._q.put_nowait(None)
            except Exception:
                pass

    def read(self, timeout: float) -> AudioChunk:
        assert self._q is not None, "Call open() first"
        item = self._q.get(timeout=timeout)  # raises queue.Empty on timeout
        if item is None:
            raise RuntimeError("Audio source closed")
        return item
