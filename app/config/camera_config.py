import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, ClassVar, List, Dict, Hashable

from app.config.config_base import ConfigBase
from app.config.variable_config import VariableValue


@dataclass
class PylonCameraConfig(ConfigBase):
    device_name: str | None = None
    config_type: Literal['preset', 'file'] = 'file'
    config_preset_name: str | None = None
    config_file_path: Path | None = None

    def get_config_file_path(self) -> Path | None:
        if self.config_type == 'preset':
            if self.config_preset_name is None:
                return None
            return Path(f"config/pylon/{self.config_preset_name}.yaml")
        elif self.config_type == 'file':
            if self.config_file_path is None:
                return None
            return self.config_file_path
        else:
            raise ValueError("Invalid config type. Must be 'preset' or 'file'.")

    def _extra_to_dict(self) -> dict:
        return {
            "device_name": self.device_name,
            "config_type": self.config_type,
            "config_preset_name": self.config_preset_name,
            "config_file_path": str(self.config_file_path.as_posix()) if self.config_file_path else None
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "device_name": data.get("device_name", cls.device_name),
            "config_type": data.get("config_type", cls.config_type),
            "config_preset_name": data.get("config_preset_name", cls.config_preset_name),
            "config_file_path": Path(data['config_file_path']) if data.get('config_file_path') else cls.config_file_path
        }

    @property
    def error(self) -> str | None:
        if self.device_name is None:
            return "Pylon device is not selected"
        return None

    @property
    def device_key(self):
        if self.device_name is None:
            return None
        return self.device_name


@dataclass
class WebcamCameraConfig(ConfigBase):
    device_index: int = 0

    def _extra_to_dict(self) -> dict:
        return {
            "device_index": self.device_index,
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "device_index": data.get("device_index", cls.device_index),
        }

    @property
    def error(self) -> str | None:
        if self.device_index < 0:
            return "Device index must be a non-negative integer"
        return None

    @property
    def device_key(self):
        return self.device_index


@dataclass
class VideoFileCameraConfig(ConfigBase):
    video_file_path: Path | None = None

    def _extra_to_dict(self) -> dict:
        return {
            "video_file_path": str(self.video_file_path.as_posix()) if self.video_file_path else None
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "video_file_path": Path(data['video_file_path']) if data.get('video_file_path') else None
        }

    @property
    def error(self) -> str | None:
        if self.video_file_path is None:
            return "Video file path is not selected"
        return None

    @property
    def device_key(self):
        if self.video_file_path is None:
            return None
        return str(self.video_file_path)


@dataclass
class CameraConfig(ConfigBase):
    CAMERA_TYPES: ClassVar[dict] = {
        'pylon': 'Pylon Camera',
        'webcam': 'Webcam',
        'video_file': 'Video File'
    }

    camera_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    camera_name: str = "New Camera"
    recording_id: str | None = None
    camera_type: Literal['pylon', 'webcam', 'video_file'] = 'pylon'

    pylon: PylonCameraConfig = field(default_factory=PylonCameraConfig)
    webcam: WebcamCameraConfig = field(default_factory=WebcamCameraConfig)
    video_file: VideoFileCameraConfig = field(default_factory=VideoFileCameraConfig)

    activated: bool = True

    variable_values: Dict[str, VariableValue] = field(default_factory=dict)

    def _extra_to_dict(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "recording_id": self.recording_id,
            "camera_type": self.camera_type,
            "pylon": self.pylon.to_dict() if self.pylon else None,
            "webcam": self.webcam.to_dict() if self.webcam else None,
            "video_file": self.video_file.to_dict() if self.video_file else None,
            "activated": self.activated,
            "variable_values": {key: value.to_dict() for key, value in self.variable_values.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "camera_id": data["camera_id"],
            "camera_name": data.get("camera_name", cls.camera_name),
            "recording_id": data.get("recording_id", cls.recording_id),
            "camera_type": data.get("camera_type", cls.camera_type),
            "pylon": PylonCameraConfig.from_dict(data.get("pylon", {})),
            "webcam": WebcamCameraConfig.from_dict(data.get("webcam", {})),
            "video_file": VideoFileCameraConfig.from_dict(data.get("video_file", {})),
            "activated": data.get("activated", cls.activated),
            "variable_values": {key: VariableValue.from_dict(value) for key, value in data.get("variable_values", {}).items()}
        }

    @property
    def active_config(self):
        if self.camera_type == 'pylon':
            return self.pylon
        elif self.camera_type == 'video_file':
            return self.video_file
        elif self.camera_type == 'webcam':
            return self.webcam
        else:
            raise ValueError(f"Unknown camera type: {self.camera_type}")

    @property
    def error(self) -> str | None:
        if self.camera_type not in self.CAMERA_TYPES:
            return f"Unknown camera type: {self.camera_type}"
        return self.active_config.error

    @property
    def device_key(self):
        if self.camera_type not in self.CAMERA_TYPES:
            return None
        subkey = self.active_config.device_key
        if subkey is None:
            return None
        return self.camera_type + ":" + str(subkey)


@dataclass
class CameraConfigList(ConfigBase):
    cameras: Dict[str, CameraConfig] = field(default_factory=dict)

    def _extra_to_dict(self):
        return {
            "cameras": {camera_id: camera.to_dict() for camera_id, camera in self.cameras.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "cameras": {camera_id: CameraConfig.from_dict(camera_data) for camera_id, camera_data in data.get("cameras", {}).items()}
        }
