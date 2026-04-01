from dataclasses import dataclass
from typing import Literal

from flow3r.core.config.abc.config import ConfigBase


@dataclass
class RecordingConfig(ConfigBase):
    recording_mode: Literal['manual', 'timed'] = 'manual'
    recording_duration: float = 60.0 * 10 # Default to 10 minutes
