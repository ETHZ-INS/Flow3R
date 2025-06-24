from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class PylonCameraConfig:
    device_name: str | None = None
    config_type: Literal['preset', 'file'] = 'preset'
    config_preset_name: str | None = None
    config_file_path: Path | None = None

    def get_config_file_path(self) -> Path:
        if self.config_file_path is not None:
            return self.config_file_path
        elif self.config_preset_name is not None:
            # Resolve default config file path based on config_preset_name
            return Path(f"config/pylon/{self.config_preset_name}.yaml")
        else:
            raise ValueError("Either config_file_path or config_preset_name must be provided.")

    def to_dict(self) -> dict:
        return {
            "device_name": self.device_name,
            "config_preset_name": self.config_preset_name,
            "config_file_path": str(self.config_file_path.as_posix()) if self.config_file_path else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PylonCameraConfig':
        return cls(
            device_name=data['device_name'],
            config_type=data['config_type'],
            config_preset_name=data.get('config_preset_name'),
            config_file_path=Path(data['config_file_path']) if data.get('config_file_path') else None
        )


@dataclass
class VideoFileCameraConfig:
    video_file_path: Path | None = None

    def to_dict(self) -> dict:
        return {
            "video_file_path": str(self.video_file_path.as_posix())
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoFileCameraConfig':
        return cls(
            video_file_path=Path(data['video_file_path'])
        )


@dataclass
class CameraConfig:
    camera_id: str
    camera_name: str
    recording_id: str | None
    camera_type: Literal['pylon', 'video_file']

    pylon: PylonCameraConfig = field(default_factory=PylonCameraConfig)
    video_file: VideoFileCameraConfig = field(default_factory=VideoFileCameraConfig)

    def to_dict(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "recording_id": self.recording_id,
            "camera_type": self.camera_type,
            "pylon": self.pylon.to_dict() if self.pylon else None,
            "video_file": self.video_file.to_dict() if self.video_file else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CameraConfig':
        return cls(
            camera_id=data['camera_id'],
            camera_name=data['camera_name'],
            recording_id=data.get('recording_id'),
            camera_type=data['camera_type'],
            pylon=PylonCameraConfig.from_dict(data['pylon']) if data.get('pylon') else PylonCameraConfig(),
            video_file=VideoFileCameraConfig.from_dict(data['video_file']) if data.get('video_file') else VideoFileCameraConfig()
        )
