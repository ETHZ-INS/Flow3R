from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Dict

from app.config.camera_config import CameraConfigList
from app.config.config_base import ConfigBase
from app.config.pipeline_config import PipelineConfigList
from app.config.recording_config import RecordingConfigList
from app.config.variable_config import VariableConfigList, VariableValue
from app.placeholder_context import PlaceholderContext


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

    def get_required_placeholders(self, recording_id: str):
        recording_config = self.recording_config_list.recordings.get(recording_id)
        if recording_config:
            camera_configs = [camera for camera in self.camera_config_list.cameras.values() if
                              camera.activated and camera.recording_id == recording_id]
            pipeline_configs = [self.pipeline_config_list.pipelines.get(camera.camera_id) for camera in
                                camera_configs]
        else:
            camera_config = self.camera_config_list.cameras.get(recording_id)
            if not camera_config:
                raise ValueError(f"Recording not found: {recording_id}")
            pipeline_configs = [self.pipeline_config_list.pipelines.get(camera_config.camera_id)]

        required_placeholders = set()
        for pipeline_config in pipeline_configs:
            if pipeline_config:
                required_placeholders.update(pipeline_config.get_required_variables())

        return list(required_placeholders)

    def get_placeholder_context(self, recording_id: str = None, preview: bool = False):
        camera_values = {}
        recording_values = {}
        if recording_id:
            recording_config = self.recording_config_list.recordings.get(recording_id)
            if recording_config:
                recording_values = recording_config.variable_values
            else:
                camera_config = self.camera_config_list.cameras.get(recording_id)
                if not camera_config:
                    raise ValueError(f"Recording not found: {recording_id}")

                camera_values = camera_config.variable_values if camera_config else {}
                print("Camera Values:", camera_values)

                recording_config = None
                if camera_config.recording_id:
                    recording_config = self.recording_config_list.recordings.get(camera_config.recording_id)

                if recording_config:
                    recording_values = recording_config.variable_values
                else:
                    recording_values = camera_values

        project_values = self.variable_values

        values = {}
        for var_id, var_config in self.variable_config_list.variables.items():
            var_name = var_config.variable_name
            var_value = None

            print("Variable ID:", var_id)
            print("Variable Name:", var_name)
            print("Variable Scope:", var_config.scope)

            if var_config.scope == "project":
                var_value = project_values.get(var_id)
            elif var_config.scope == "group":
                var_value = recording_values.get(var_id)
            elif var_config.scope == "camera":
                var_value = camera_values.get(var_id)

            print("Variable Value:", var_value)

            if var_value is not None and var_value.value is not None:
                values[var_config.variable_name] = var_value.value
            elif preview:
                values[var_config.variable_name] = var_config.example_value

        print("Collected values:", values)

        placeholders = deepcopy(list(self.variable_config_list.variables.values()))
        return PlaceholderContext(values)
