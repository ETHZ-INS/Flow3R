from pathlib import Path
from typing import Callable, Optional, Protocol


from flow3r.core.streaming.abc.sink import Sink
from flow3r.plugins.core.pipeline.util.soundfile_writer import SoundFileWriter
from flow3r.plugins.core.typing.audio import AudioFormat, AudioChunk


class IAudioWriter(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, chunk: AudioChunk) -> None: ...


AudioWriterFactory = Callable[[Path, AudioFormat], IAudioWriter]


def default_audio_writer_factory(audio_file: Path, desc: AudioFormat):
    return SoundFileWriter(audio_file, desc.sample_rate, desc.channels)


class AudioWriterSink(Sink[AudioFormat, AudioChunk]):
    def __init__(self, audio_file: Path, factory: AudioWriterFactory = default_audio_writer_factory):
        super().__init__()
        self._audio_file = audio_file
        self._factory = factory
        self._writer: Optional[IAudioWriter] = None

    def setup(self, desc: AudioFormat) -> None:
        try:
            self._writer = self._factory(self._audio_file, desc)
            self._writer.open()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def on_next(self, item: AudioChunk) -> None:
        assert self._writer is not None
        self._writer.write(item)

    def cleanup(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None
