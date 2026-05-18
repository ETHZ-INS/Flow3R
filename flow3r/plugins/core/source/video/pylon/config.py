from dataclasses import dataclass
from typing import ClassVar, Optional

from flow3r.core.source.abc.source_config import SourceConfigBase


@dataclass
class PylonCameraSourceConfig(SourceConfigBase):
    TYPE_ID: ClassVar[str] = "core.source.video.pylon"
    VERSION: ClassVar[int] = 1

    device: Optional[str] = None
    config_file: Optional[str] = None
