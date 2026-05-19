from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Type

from flow3r.core.config.abc.config import ConfigBase, ITypedConfig


@dataclass
class RecordingConfig(ConfigBase):
    VERSION = 1

    recording_mode: Literal['manual', 'timed'] = 'manual'
    recording_duration: float = 60.0 * 10  # Default to 10 minutes
    shortcut_key: Optional[str] = None  # Key sequence string, e.g. "F5" or "Ctrl+A"

    def _to_dict_data(self) -> Dict[str, Any]:
        return {
            "recording_mode": self.recording_mode,
            "recording_duration": self.recording_duration,
            "shortcut_key": self.shortcut_key,
        }

    @classmethod
    def _from_dict_data(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> "RecordingConfig":
        return cls(
            recording_mode=data["recording_mode"],
            recording_duration=data["recording_duration"],
            shortcut_key=data.get("shortcut_key"),  # graceful fallback for old files
        )

