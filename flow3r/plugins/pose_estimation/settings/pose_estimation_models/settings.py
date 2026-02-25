import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Hashable


@dataclass
class PoseEstimationModelConfig:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Model"
    model_identifier: str = ""

    @property
    def key(self) -> Hashable:
        # For pose service to know if two models are the same
        return self.model_identifier


@dataclass
class PoseEstimationModelsSettings:
    models: OrderedDict[str, PoseEstimationModelConfig] = field(default_factory=OrderedDict)
