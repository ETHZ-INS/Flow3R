from pathlib import Path

from reactivex import operators as ops

from reactivex.subject import ReplaySubject

from aaaflow3r.core.source.abc.source import ISource
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.plugins.core.source.audio.audio_file.config import AudioFileSourceConfig
from aaaflow3r.plugins.core.source.audio.util.soundfile_source import SoundFileSource
from aaaflow3r.plugins.core.source.video.source_observable import source_observable
from aaaflow3r.plugins.core.typing.audio import AudioChunk, AudioFormat


class AudioFileSource(ISource[AudioFormat, AudioChunk]):
    def __init__(self, config: AudioFileSourceConfig):
        self._config = config

        self._recorder = SoundFileSource(
            path=Path(config.file_path),
            chunk_size=1600,
            playback=True
        )

        self._desc_subject = ReplaySubject(1)
        self._frame_observable = source_observable(self._recorder).pipe(ops.share())
        self._stream = Stream(self._desc_subject, self._frame_observable)

    @property
    def stream(self) -> Stream[AudioFormat, AudioChunk]:
        return self._stream

    def open(self):
        desc = AudioFormat(
            sample_rate=self._recorder.sample_rate,
            channels=self._recorder.channels,
            sample_format="f32",
            chunk_size=1600
        )
        self._desc_subject.on_next(desc)

    def close(self):
        self._desc_subject.on_completed()
