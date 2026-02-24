from reactivex import operators as ops

from reactivex.subject import ReplaySubject

from flow3r.core.source.abc.source import ISource
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.source.audio.microphone.config import MicrophoneSourceConfig
from flow3r.plugins.core.source.audio.util.sounddevice_microphone_source import \
    SoundDeviceMicrophoneSource
from flow3r.plugins.core.source.video.source_observable import source_observable
from flow3r.plugins.core.typing.audio import AudioChunk, AudioFormat


class MicrophoneSource(ISource[AudioFormat, AudioChunk]):
    def __init__(self, config: MicrophoneSourceConfig):
        self._config = config

        self._recorder = SoundDeviceMicrophoneSource(
            device=config.device_index,
            channels=config.num_channels,
            samplerate=config.sample_rate,
            chunk_size=1600
        )

        self._desc_subject = ReplaySubject(1)
        self._frame_observable = source_observable(self._recorder).pipe(ops.share())
        self._stream = Stream(self._desc_subject, self._frame_observable)

    @property
    def stream(self) -> Stream[AudioFormat, AudioChunk]:
        return self._stream

    def open(self):
        desc = AudioFormat(
            sample_rate=self._config.sample_rate,
            channels=self._config.num_channels,
            sample_format="f32",
            chunk_size=1600
        )
        self._desc_subject.on_next(desc)

    def close(self):
        self._desc_subject.on_completed()
