import uuid
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Optional, Set

from flow3r.app.config.recording_config import RecordingConfig


@dataclass
class GroupConfig:
    RECORDING_MODES: ClassVar[Dict[str, str]] = {
        'manual': 'Manual',
        'timed': 'Timed'
    }

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Group"
    implicit: bool = False
    active: bool = True
    recording_config: RecordingConfig = field(default_factory=RecordingConfig)
    pipeline_id: Optional[str] = None

    pipeline_ids: Set[str] = field(default_factory=set)
    source_mapping: Dict[str, Dict[str, str]] = field(default_factory=dict)  # pipeline_id -> input_name -> source_id
