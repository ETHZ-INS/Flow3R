from dataclasses import dataclass, field
from typing import Dict

from app.config.camera_config import CameraConfig
from app.config.recording_config import RecordingConfig


@dataclass(kw_only=True)
class WelfareRecorderConfig:
    cameras: Dict[str, CameraConfig] = field(default_factory=dict, init=False)
    default_recording: RecordingConfig = field(default_factory=lambda: RecordingConfig(recording_id="default", recording_name="Default"), init=False)
    recordings: Dict[str, RecordingConfig] = field(default_factory=dict, init=False)

    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, data):
        return cls()
