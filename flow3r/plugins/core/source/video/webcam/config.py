from dataclasses import dataclass

from flow3r.core.source.abc.source_config import SourceConfigBase


@dataclass
class WebcamSourceConfig(SourceConfigBase):
    TYPE_ID = "core.source.video.webcam"
    VERSION = 1

    device_index: int = 0
    grayscale: bool = False
