from dataclasses import dataclass


@dataclass
class MicrophoneSourceConfig:
    device_index: int = 0
