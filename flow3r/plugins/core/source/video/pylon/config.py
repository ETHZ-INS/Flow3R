from dataclasses import dataclass
from typing import Optional


@dataclass
class PylonCameraSourceConfig:
    device: Optional[str] = None
    config_file: Optional[str] = None
