import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, List, Tuple

from app.config.config_base import ConfigBase


@dataclass
class PoseEstimationModelConfig(ConfigBase):
    MODEL_TYPES: ClassVar[dict] = {
        "yolo_3r_hub": "YOLO (3R Hub Format)",
        "yolo_original": "YOLO (Original Format)"
    }

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = "New Model"
    type: str = "yolo_3r_hub"
    folder: Path = None

    @property
    def location(self) -> List[str]:
        return ["pose_estimation_model", self.id]

    @property
    def error(self) -> Tuple[List[str], str] | None:
        if not self.id:
            return self.location, "Pose estimation model ID is empty."
        if not self.name:
            return self.location, "Pose estimation model name is empty."
        if self.type not in self.MODEL_TYPES:
            return self.location, "Invalid pose estimation model type."
        if not self.folder:
            return self.location, "Pose estimation model folder is not selected."
        return None

    def _extra_to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "folder": self.folder.as_posix() if self.folder else None
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "id": data.get("id", uuid.uuid4().hex),
            "name": data.get("name", cls.name),
            "type": data.get("type", cls.type),
            "folder": Path(data['folder']) if data.get('folder') else cls.folder
        }


@dataclass
class PoseEstimationPresetConfig(ConfigBase):
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = "New Preset"
    models: List[str] = field(default_factory=list)  # List of PoseEstimationModelConfig ids
    tracked_instances: List[str] = field(default_factory=list)

    @property
    def location(self) -> List[str]:
        return ["pose_estimation_preset", self.id]

    @property
    def error(self) -> Tuple[List[str], str] | None:
        if not self.id:
            return self.location, "Pose estimation preset ID is empty."
        if not self.name:
            return self.location, "Pose estimation preset name is empty."
        for model_id in self.models:
            if not model_id:
                return self.location, "One of the pose estimation model IDs in the preset is empty."
        return None

    def _extra_to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "models": self.models,
            "tracked_instances": self.tracked_instances
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "id": data.get("id", uuid.uuid4().hex),
            "name": data.get("name", cls.name),
            "models": data.get("models", []),
            "tracked_instances": data.get("tracked_instances", [])
        }