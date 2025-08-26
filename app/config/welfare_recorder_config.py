from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Dict

from app.config.camera_config import CameraConfigList
from app.config.config_base import ConfigBase
from app.config.pipeline_config import PipelineConfigList
from app.config.recording_config import RecordingConfigList
from app.config.variable_config import VariableConfigList, VariableValue


@dataclass
class WelfareRecorderConfig(ConfigBase):
    camera_config_list: CameraConfigList = field(default_factory=CameraConfigList)
    recording_config_list: RecordingConfigList = field(default_factory=RecordingConfigList)
    pipeline_config_list: PipelineConfigList = field(default_factory=PipelineConfigList)  # TODO: Make sure every camera has a pipeline config
    variable_config_list: VariableConfigList = field(default_factory=VariableConfigList)

    variable_values: Dict[str, VariableValue] = field(default_factory=dict)

    INTERNAL_MODELS: ClassVar[dict] = {
        "Mouse": Path("D:/Experiments/UnifiedTrackingModel/ActualProperSplit/MouseV5_2_HQAmp2"),
        "Environment": Path("D:/Experiments/UnifiedTrackingModel/ActualProperSplit/EnvironmentV5_HE1_Reoriented"),
    }

    def _extra_to_dict(self):
        return {
            "camera_config_list": self.camera_config_list.to_dict(),
            "recording_config_list": self.recording_config_list.to_dict(),
            "pipeline_config_list": self.pipeline_config_list.to_dict(),
            "variable_config_list": self.variable_config_list.to_dict(),
            "variable_values": {k: v.to_dict() for k, v in self.variable_values.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data):
        return {
            "camera_config_list": CameraConfigList.from_dict(data.get("camera_config_list", {})),
            "recording_config_list": RecordingConfigList.from_dict(data.get("recording_config_list", {})),
            "pipeline_config_list": PipelineConfigList.from_dict(data.get("pipeline_config_list", {})),
            "variable_config_list": VariableConfigList.from_dict(data.get("variable_config_list", {})),
            "variable_values": {k: VariableValue.from_dict(v) for k, v in data.get("variable_values", {}).items()}
        }
