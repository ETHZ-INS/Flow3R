from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Protocol

from aaaflow3r.core.streaming.abc.finalize_transform import FinalizeTransform
from aaaflow3r.plugins.core.pipeline.util.soundfile_writer import SoundFileWriter
from aaaflow3r.plugins.core.typing.audio import AudioFormat, AudioChunk

# Import your FinalizeTransform base (as discussed)
# from aaaflow3r.core.streaming.abc.transform import FinalizeTransform


class IAudioWriter(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, chunk: AudioChunk) -> None: ...


AudioWriterFactory = Callable[[Path, AudioFormat], IAudioWriter]


def default_audio_writer_factory(audio_file: Path, desc: AudioFormat) -> IAudioWriter:
    return SoundFileWriter(audio_file, desc.sample_rate, desc.channels)


class AudioWriterTransform(FinalizeTransform[AudioFormat, AudioChunk, Path, Path]):
    """
    Transform that writes AudioChunk items to disk and emits the audio file Path exactly once
    when the upstream completes (and optionally also when disposed).

    - Input descriptor: AudioFormat
    - Output descriptor: Path (the output file path)
    - Output data: Path (emitted once at finalize)
    """

    def __init__(self, audio_file: Path, factory: AudioWriterFactory = default_audio_writer_factory):
        super().__init__()
        self._audio_file = audio_file
        self._factory = factory
        self._writer: Optional[IAudioWriter] = None

    def infer_descriptor(self, desc_in: AudioFormat) -> Path:
        # Downstream nodes can learn the final artifact path immediately.
        return self._audio_file

    def setup(self, desc_in: AudioFormat) -> None:
        # Create/open the writer once we know the audio format.
        self._writer = self._factory(self._audio_file, desc_in)
        self._writer.open()

    def on_item(self, item: AudioChunk) -> None:
        # Called for each chunk.
        assert self._writer is not None
        self._writer.write(item)

    def finalize(self) -> Path:
        # Called exactly once by FinalizeTransform (on_completed, and on dispose if enabled).
        if self._writer is not None:
            try:
                self._writer.close()
            finally:
                self._writer = None
        return self._audio_file

    def cleanup(self) -> None:
        # Defensive: if something bypassed finalize (e.g., errors), make sure we close.
        if self._writer is not None:
            try:
                self._writer.close()
            finally:
                self._writer = None
