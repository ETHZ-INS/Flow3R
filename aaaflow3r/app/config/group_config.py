import uuid
from dataclasses import dataclass, field
from typing import ClassVar, Dict

from aaaflow3r.app.config.recording_config import RecordingConfig


@dataclass
class GroupConfig:
    RECORDING_MODES: ClassVar[Dict[str, str]] = {
        'manual': 'Manual',
        'timed': 'Timed'
    }

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Group"
    active: bool = True
    recording_config: RecordingConfig = field(default_factory=RecordingConfig)
    pipeline_id: str = None
