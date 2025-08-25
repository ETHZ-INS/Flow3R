import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from app.config.config_base import ConfigBase


@dataclass
class PoseEstimationModelConfig(ConfigBase):
    model_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    external: bool = False
    internal_model_name: str = None
    model_folder: Path = None
    device: str = "cuda"
    save_to_file: bool = True
    save_file_template: str = "{base_folder}/{recording_name}/{camera_name}_pose_results.csv"

    @property
    def name(self) -> str:
        if self.external:
            model_name = self.model_folder.name if self.model_folder else "New Model"
        else:
            model_name = self.internal_model_name if self.internal_model_name else "New Model"
        return f"{model_name} ({self.device})"

    def _extra_to_dict(self):
        return {
            'model_id': self.model_id,
            'external': self.external,
            'internal_model_name': self.internal_model_name,
            'model_folder': str(self.model_folder) if self.model_folder else None,
            'device': self.device,
            'save_to_file': self.save_to_file,
            'save_file_template': self.save_file_template
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "model_id": data["model_id"],
            "external": data.get('external', cls.external),
            "internal_model_name": data.get('internal_model_name', cls.internal_model_name),
            "model_folder": Path(data['model_folder']) if data.get('model_folder') else cls.model_folder,
            "device": data.get('device', cls.device),
            "save_to_file": data.get('save_to_file', cls.save_to_file),
            "save_file_template": data.get('save_file_template', cls.save_file_template)
        }


@dataclass
class PoseEstimationConfig(ConfigBase):
    models: Dict[str, PoseEstimationModelConfig] = field(default_factory=dict)

    def _extra_to_dict(self) -> dict:
        return {
            "models": {model_id: model.to_dict() for model_id, model in self.models.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "models": {model_id: PoseEstimationModelConfig.from_dict(model_data) for model_id, model_data in data.get("models", {}).items()}
        }
