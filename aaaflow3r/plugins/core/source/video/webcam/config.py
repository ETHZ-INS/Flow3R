from dataclasses import dataclass


@dataclass
class WebcamSourceConfig:
    device_index: int = 0
