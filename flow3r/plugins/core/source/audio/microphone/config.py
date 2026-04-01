from dataclasses import dataclass

from flow3r.core.source.abc.source_config import SourceConfigBase


@dataclass
class MicrophoneSourceConfig(SourceConfigBase):
    TYPE_ID = "core.source.audio.microphone"
    VERSION = 1

    device_index: int = 0
    num_channels: int = 1
    sample_rate: int = 48_000
    chunk_size: int = 1600
