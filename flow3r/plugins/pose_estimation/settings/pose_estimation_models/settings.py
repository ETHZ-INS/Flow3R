import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Hashable, Dict, Any, Type, Self

from flow3r.core.config.abc.config import ConfigBase, ITypedConfig
from flow3r.core.settings.abc.settings_config import SettingsBase


@dataclass
class PoseEstimationModelConfig(ConfigBase):
    VERSION = 1

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Model"
    model_identifier: str = ""

    @property
    def key(self) -> Hashable:
        # For pose service to know if two models are the same
        return self.model_identifier


@dataclass
class PoseEstimationModelsSettings(SettingsBase):
    TYPE_ID = "pose_estimation.settings.pose_estimation_models"
    VERSION = 1

    models: OrderedDict[str, PoseEstimationModelConfig] = field(default_factory=OrderedDict)

    def _to_dict_data(self) -> Dict[str, Any]:
        return {
            "models": [model.to_dict() for model in self.models.values()]
        }

    @classmethod
    def _from_dict_data(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> Self:
        models = OrderedDict()
        for model_data in data["models"]:
            model = PoseEstimationModelConfig.from_dict(model_data, type_registry)
            models[model.id] = model
        return cls(models=models)
