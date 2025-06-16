from dataclasses import dataclass, field
from typing import Dict

from app.config.camera_config import CameraConfig


@dataclass(kw_only=True)
class WelfareRecorderConfig:
    cameras: Dict[str, CameraConfig] = field(default_factory=dict, init=False)

    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, data):
        return cls()
