from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Dict, List

from app.config.camera_config import CameraConfigList, CameraConfig
from app.config.config_base import ConfigBase
from app.config.pipeline_config import PipelineConfigList, PipelineConfig
from app.config.recording_config import RecordingConfigList, RecordingConfig
from app.config.variable_config import VariableConfigList, VariableValue, VariableConfig
from app.placeholder_context import PlaceholderContext


@dataclass
class WelfareRecorderConfig(ConfigBase):
    camera_config_list: CameraConfigList = field(default_factory=CameraConfigList)
    recording_config_list: RecordingConfigList = field(default_factory=RecordingConfigList)
    pipeline_config_list: PipelineConfigList = field(default_factory=PipelineConfigList)
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

    def _get_virtual_recording_config(self, camera_id: str):
        # Create a virtual recording config for the given camera based on the default recording config
        camera_config = self.camera_config_list.cameras.get(camera_id)
        if not camera_config:
            raise ValueError(f"Camera not found: {camera_id}")

        recording_config = deepcopy(self.recording_config_list.default_recording)
        recording_config.recording_id = camera_id
        recording_config.variable_values = deepcopy(camera_config.variable_values)

        return recording_config

    def get_camera_view(self, camera_id: str):
        # Gets a narrowed view of the config for the given camera (Useful for placeholder resolution)
        camera_config = self.camera_config_list.cameras.get(camera_id)
        if not camera_config:
            raise ValueError(f"Camera not found: {camera_id}")

        if camera_config.recording_id:
            recording_config = self.recording_config_list.recordings.get(camera_config.recording_id)
            if not recording_config:
                raise ValueError(f"Recording not found: {camera_config.recording_id}")
        else:
            recording_config = self._get_virtual_recording_config(camera_id)

        pipeline_config = self.pipeline_config_list.pipelines.get(camera_id)
        if not pipeline_config:
            raise ValueError(f"Pipeline not found for camera: {camera_id}")

        placeholders = list(self.variable_config_list.variables.values())

        return CameraConfigView(
            project=self,
            camera=camera_config,
            recording=recording_config,
            pipeline=pipeline_config,
            placeholders=placeholders
        )

    def get_recording_view(self, recording_id: str):
        # Gets a narrowed view of the config for the given recording (Useful for placeholder resolution)
        recording_config = self.recording_config_list.recordings.get(recording_id)
        if recording_config:
            camera_configs = [c for c in self.camera_config_list.cameras.values() if c.activated and c.recording_id == recording_id]
        else:
            camera_config = self.camera_config_list.cameras.get(recording_id)
            if not camera_config:
                raise ValueError(f"Recording not found: {recording_id}")
            recording_config = self._get_virtual_recording_config(recording_id)
            camera_configs = [camera_config]

        camera_views = [self.get_camera_view(c.camera_id) for c in camera_configs]
        placeholders = list(self.variable_config_list.variables.values())

        return RecordingConfigView(
            project=self,
            recording=recording_config,
            camera_views=camera_views,
            placeholders=placeholders
        )


@dataclass
class CameraConfigView:
    project: WelfareRecorderConfig
    camera: CameraConfig
    recording: RecordingConfig  # Associated recording config if recording_id is set, otherwise a virtual recording config with default recording settings
    pipeline: PipelineConfig
    placeholders: List[VariableConfig] = field(default_factory=list)

    def get_required_placeholders(self):
        return self.pipeline.get_required_variables()

    def get_placeholder_context(self, preview: bool = False):
        values = {}
        for placeholder in self.placeholders:
            value = None
            if placeholder.scope == "project":
                value = self.project.variable_values.get(placeholder.variable_id)
            elif placeholder.scope == "group":
                value = self.recording.variable_values.get(placeholder.variable_id)
            elif placeholder.scope == "camera":
                value = self.camera.variable_values.get(placeholder.variable_id)

            if value is not None and value.value is not None:
                values[placeholder.variable_name] = value.value
            elif preview:
                values[placeholder.variable_name] = placeholder.example_value

        return PlaceholderContext(values)


@dataclass
class RecordingConfigView:
    project: WelfareRecorderConfig
    recording: RecordingConfig
    camera_views: List[CameraConfigView] = field(default_factory=list)
    placeholders: List[VariableConfig] = field(default_factory=list)
