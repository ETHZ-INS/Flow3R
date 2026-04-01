from dataclasses import dataclass
from typing import Optional

from flow3r.core.source.abc.source_config import SourceConfigBase


@dataclass
class PylonCameraSourceConfig(SourceConfigBase):
    TYPE_ID = "core.source.video.pylon"
    VERSION = 1

    device: Optional[str] = None
    config_file: Optional[str] = None
