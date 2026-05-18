from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Dict, Any, Self, Type, Optional, Tuple

from flow3r.core.config.abc.config import ITypedConfig
from flow3r.core.source.abc.source_config import SourceConfigBase


class FrameSizeSetting(str, Enum):
    DEFAULT = "default"
    PRESET = "preset"
    CUSTOM = "custom"


# Common frame size presets (width, height)
FRAME_SIZE_PRESETS: list[Tuple[int, int]] = [
    (640, 480),
    (800, 600),
    (1280, 720),
    (1920, 1080),
    (2560, 1440),
    (3840, 2160),
]


@dataclass
class WebcamSourceConfig(SourceConfigBase):
    TYPE_ID: ClassVar[str] = "core.source.video.webcam"
    VERSION: ClassVar[int] = 1

    device_path: Optional[str] = None
    grayscale: bool = False

    frame_size_setting: FrameSizeSetting = FrameSizeSetting.DEFAULT
    # Used when frame_size_setting == PRESET
    frame_size_preset: Optional[Tuple[int, int]] = None
    # Used when frame_size_setting == CUSTOM
    frame_size_custom: Optional[Tuple[int, int]] = None

    @property
    def resolved_size(self) -> Optional[Tuple[int, int]]:
        """Returns the (width, height) tuple based on the current setting, or None for default."""
        if self.frame_size_setting == FrameSizeSetting.DEFAULT:
            return None
        elif self.frame_size_setting == FrameSizeSetting.PRESET:
            return self.frame_size_preset
        elif self.frame_size_setting == FrameSizeSetting.CUSTOM:
            return self.frame_size_custom
        return None

    @property
    def width(self) -> Optional[int]:
        size = self.resolved_size
        return size[0] if size else None

    @property
    def height(self) -> Optional[int]:
        size = self.resolved_size
        return size[1] if size else None

    def _to_dict_data(self) -> Dict[str, Any]:
        return {
            "device_path": self.device_path,
            "grayscale": self.grayscale,
            "frame_size_setting": self.frame_size_setting.value,
            "frame_size_preset": list(self.frame_size_preset) if self.frame_size_preset else None,
            "frame_size_custom": list(self.frame_size_custom) if self.frame_size_custom else None,
        }

    @classmethod
    def _from_dict_data(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> Self:
        preset = data.get("frame_size_preset")
        custom = data.get("frame_size_custom")
        return cls(
            device_path=data.get("device_path"),
            grayscale=data.get("grayscale", False),
            frame_size_setting=FrameSizeSetting(data.get("frame_size_setting", FrameSizeSetting.DEFAULT.value)),
            frame_size_preset=tuple(preset) if preset else None,
            frame_size_custom=tuple(custom) if custom else None,
        )
