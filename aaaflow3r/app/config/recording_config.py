from dataclasses import dataclass
from typing import Literal


@dataclass
class RecordingConfig:
    recording_mode: Literal['manual', 'timed'] = 'manual'
    recording_duration: float = 60.0 * 10 # Default to 10 minutes
