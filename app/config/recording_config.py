from dataclasses import dataclass
from typing import Literal


@dataclass
class RecordingConfig:
    recording_id: str
    recording_name: str
    recording_mode: Literal['manual', 'timed'] = 'manual'

    def to_dict(self) -> dict:
        return {
            "recording_id": self.recording_id,
            "recording_name": self.recording_name,
            "recording_mode": self.recording_mode
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RecordingConfig':
        return cls(
            recording_id=data['recording_id'],
            recording_name=data['recording_name'],
            recording_mode=data['recording_mode'] if 'recording_mode' in data else 'manual'
        )