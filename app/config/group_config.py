import uuid
from dataclasses import dataclass, field
from typing import Literal, Dict, ClassVar, List, Tuple

from app.config.config_base import ConfigBase
from app.config.variable_config import VariableValue


@dataclass
class GroupConfig(ConfigBase):
    RECORDING_MODES: ClassVar[dict] = {
        "manual": "Manual",
        "timed": "Timed",
    }

    group_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    recording_name: str = 'New Group'
    recording_mode: Literal['manual', 'timed'] = 'manual'
    recording_duration: float = 60.0 * 10 # Default to 10 minutes

    variable_values: Dict[str, VariableValue] = field(default_factory=dict)

    @property
    def is_default(self) -> bool:
        return self.group_id == 'default'

    @property
    def location(self) -> List[str]:
        return ['group', self.group_id]

    @property
    def error(self) -> Tuple[List[str], str] | None:
        if not self.group_id:
            return self.location, "Group ID id empty."
        if not self.recording_name:
            return self.location, "Recording name is empty."
        if self.recording_mode not in self.RECORDING_MODES:
            return self.location, "Invalid recording mode."
        if self.recording_mode == 'timed' and self.recording_duration <= 0:
            return self.location, "Recording duration must be positive."
        return None

    def _extra_to_dict(self):
        return {
            "group_id": self.group_id,
            "recording_name": self.recording_name,
            "recording_mode": self.recording_mode,
            "recording_duration": self.recording_duration,
            "variable_values": {var_id: var_value.to_dict() for var_id, var_value in self.variable_values.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "group_id": data["group_id"],
            "recording_name": data.get("recording_name", cls.recording_name),
            "recording_mode": data.get("recording_mode", cls.recording_mode),
            "recording_duration": data.get("recording_duration", cls.recording_duration),
            "variable_values": {var_id: VariableValue.from_dict(var_value_data) for var_id, var_value_data in data.get("variable_values", {}).items()}
        }
