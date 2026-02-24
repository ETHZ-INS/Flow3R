from __future__ import annotations

from pathlib import Path
import soundfile as sf

from flow3r.plugins.core.typing.audio import AudioChunk


class SoundFileWriter:
    """
    Streaming audio file writer.

    Supports WAV, FLAC, OGG, AIFF, etc. (anything libsndfile supports).
    """

    def __init__(
        self,
        path: Path,
        sample_rate: int,
        channels: int,
        subtype: str | None = None,  # e.g. "PCM_16", "PCM_24", "FLOAT"
    ):
        self.path = path
        self.sample_rate = sample_rate
        self.channels = channels
        self.subtype = subtype

        self._f: sf.SoundFile | None = None

    def open(self) -> None:
        self._f = sf.SoundFile(
            file=str(self.path),
            mode="w",
            samplerate=self.sample_rate,
            channels=self.channels,
            subtype=self.subtype,
        )

    def write(self, chunk: AudioChunk) -> None:
        assert self._f is not None, "Call open() first"

        samples = chunk.samples

        # Enforce shape (frames, channels)
        if samples.ndim != 2 or samples.shape[1] != self.channels:
            raise ValueError(
                f"Expected samples shape (N, {self.channels}), got {samples.shape}"
            )

        self._f.write(samples)

    def close(self) -> None:
        if self._f is not None:
            self._f.close()
        self._f = None
