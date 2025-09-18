import uuid
from dataclasses import dataclass, field
from typing import Literal, Dict, ClassVar

from app.config.config_base import ConfigBase
from app.config.variable_config import VariableValue


@dataclass
class GroupConfig(ConfigBase):
    RECORDING_MODES: ClassVar[dict] = {
        "manual": "Manual",
        "timed": "Timed",
    }

    recording_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    recording_name: str = 'New Group'
    recording_mode: Literal['manual', 'timed'] = 'manual'
    recording_duration: float = 60.0 * 10 # Default to 10 minutes

    variable_values: Dict[str, VariableValue] = field(default_factory=dict)

    @property
    def is_default(self) -> bool:
        return self.recording_id == 'default'

    def _extra_to_dict(self):
        return {
            "recording_id": self.recording_id,
            "recording_name": self.recording_name,
            "recording_mode": self.recording_mode,
            "recording_duration": self.recording_duration,
            "variable_values": {var_id: var_value.to_dict() for var_id, var_value in self.variable_values.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "recording_id": data["recording_id"],
            "recording_name": data.get("recording_name", cls.recording_name),
            "recording_mode": data.get("recording_mode", cls.recording_mode),
            "recording_duration": data.get("recording_duration", cls.recording_duration),
            "variable_values": {var_id: VariableValue.from_dict(var_value_data) for var_id, var_value_data in data.get("variable_values", {}).items()}
        }
