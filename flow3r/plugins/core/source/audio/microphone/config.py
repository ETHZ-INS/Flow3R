from dataclasses import dataclass


@dataclass
class MicrophoneSourceConfig:
    device_index: int = 0
    num_channels: int = 1
    sample_rate: int = 48_000
    chunk_size: int = 1600
