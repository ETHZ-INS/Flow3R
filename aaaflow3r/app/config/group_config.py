import uuid
from dataclasses import dataclass, field

from aaaflow3r.app.config.recording_config import RecordingConfig


@dataclass
class GroupConfig:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Group"
    recording_config: RecordingConfig = field(default_factory=RecordingConfig)
