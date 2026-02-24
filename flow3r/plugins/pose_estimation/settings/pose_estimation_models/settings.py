import uuid
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class PoseEstimationModelConfig:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Model"
    model_identifier: str = ""


@dataclass
class PoseEstimationModelsSettings:
    models: OrderedDict[str, PoseEstimationModelConfig] = field(default_factory=OrderedDict)
