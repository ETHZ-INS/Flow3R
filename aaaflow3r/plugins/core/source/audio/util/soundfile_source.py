from __future__ import annotations

from pathlib import Path
import time
from typing import Optional

import soundfile as sf
import numpy as np

from aaaflow3r.plugins.core.typing.audio import AudioChunk


class SoundFileSource:
    """
    File-backed audio source that emits AudioChunk(timestamp, samples).

    If playback=True, chunks are paced so that chunk.timestamp is emitted
    at real-time speed relative to open().

    Timeout behavior in playback mode:
      - If timeout is not None and the next chunk is not yet "due",
        read() will sleep up to `timeout` seconds and then raise TimeoutError.
        (Callers should treat TimeoutError like a normal "try again".)
    """

    def __init__(
        self,
        path: Path,
        chunk_size: int = 1600,
        dtype: str = "float32",
        playback: bool = False,
    ):
        self.path = path
        self.chunk_size = chunk_size
        self.dtype = dtype
        self.playback = playback

        self._sample_rate: int | None = None
        self._channels: int | None = None

        self._f: sf.SoundFile | None = None
        self._frames_read: int = 0
        self._t0: float | None = None  # perf_counter baseline for playback pacing

        self._probe()

    @property
    def sample_rate(self) -> int:
        assert self._sample_rate is not None
        return self._sample_rate

    @property
    def channels(self) -> int:
        assert self._channels is not None
        return self._channels

    def open(self) -> None:
        self._f = sf.SoundFile(str(self.path), mode="r")
        self._frames_read = 0
        self._t0 = time.perf_counter()  # start "playback clock" at open()

    def close(self) -> None:
        if self._f is not None:
            self._f.close()
        self._f = None
        self._t0 = None

    def read(self, timeout: float) -> AudioChunk:
        """
        Returns the next AudioChunk.

        In non-playback mode, timeout is ignored (file reads are immediate).

        In playback mode, this may raise TimeoutError if the chunk is scheduled
        in the future and timeout elapses before it is due.
        """
        assert self._f is not None and self._sample_rate is not None, "Call open() first"

        start_timestamp = self._frames_read / self._sample_rate

        if self.playback:
            assert self._t0 is not None
            self._pace_to_timestamp(start_timestamp, timeout)

        samples = self._f.read(self.chunk_size, dtype=self.dtype, always_2d=True)
        # always_2d=True ensures shape (frames, channels)

        if samples.size == 0:
            raise EOFError("End of file")

        self._frames_read += samples.shape[0]

        # Ensure np.ndarray (soundfile returns np.ndarray already, but keep it explicit)
        if not isinstance(samples, np.ndarray):
            samples = np.asarray(samples)

        return AudioChunk(timestamp=float(start_timestamp), samples=samples)

    def _probe(self) -> None:
        info = sf.info(str(self.path))
        self._sample_rate = int(info.samplerate)
        self._channels = int(info.channels)

    def _pace_to_timestamp(self, ts: float, timeout: Optional[float]) -> None:
        """
        Sleep until the wall-clock time corresponding to the audio timestamp ts.

        If timeout is not None, sleep up to timeout; if still early, raise TimeoutError
        so caller can retry (and remain responsive to shutdown).
        """
        assert self._t0 is not None
        target = self._t0 + ts

        now = time.perf_counter()
        remaining = target - now
        if remaining <= 0:
            return

        if timeout is None:
            time.sleep(remaining)
            return

        # sleep in at most `timeout` seconds, then report "not ready yet"
        if remaining > timeout:
            time.sleep(timeout)
            raise TimeoutError("Playback pacing: chunk not ready yet")
        else:
            time.sleep(remaining)
