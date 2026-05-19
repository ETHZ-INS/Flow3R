from reactivex import operators as ops

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

        fmt = AudioFormat(
            sample_rate=self._config.sample_rate,
            channels=self._config.num_channels,
            sample_format="f32",
            chunk_size=1600
        )

        data = source_observable(self._recorder).pipe(ops.share())
        self._stream = Stream(fmt, data)

    @property
    def stream(self) -> Stream[AudioFormat, AudioChunk]:
        return self._stream

    def open(self):
        pass

    def close(self):
        pass
