from collections import OrderedDict
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import ClassVar, Dict, Tuple, List

from app.config.camera_config import CameraConfig
from app.config.config_base import ConfigBase
from app.config.pipeline_config import PipelineConfig
from app.config.recording_config import GroupConfig
from app.config.variable_config import VariableValue, VariableConfig
from app.placeholder_context import PlaceholderContext


@dataclass
class CameraConfigView:
    group_id: str
    project: "WelfareRecorderConfig"
    camera: CameraConfig
    pipeline: PipelineConfig
    placeholders: List[VariableConfig]
    placeholder_context: PlaceholderContext
    preview_placeholder_context: PlaceholderContext

    def get_required_placeholders(self) -> set[str]:
        required_placeholders = self.pipeline.get_required_placeholders()
        for placeholder in list(required_placeholders):
            dependencies = self.placeholder_context.dependencies(placeholder)
            required_placeholders.update(dependencies)
        return required_placeholders


@dataclass
class GroupConfigView:
    group_id: str
    group: GroupConfig
    cameras: List[CameraConfigView]
    placeholders: List[VariableConfig]


@dataclass
class WelfareRecorderConfig(ConfigBase):
    cameras: OrderedDict[str, CameraConfig] = field(default_factory=OrderedDict)
    groups: OrderedDict[str, GroupConfig] = field(default_factory=lambda : OrderedDict({'default': GroupConfig(recording_id='default', recording_name='Default (Individual)', locked_values={"self", "recording_name"})}))
    pipelines: OrderedDict[str, PipelineConfig] = field(default_factory=OrderedDict)
    placeholders: OrderedDict[str, VariableConfig] = field(default_factory=OrderedDict)

    values: Dict[str, VariableValue] = field(default_factory=dict)

    INTERNAL_MODELS: ClassVar[dict] = {
        "Mouse": Path("D:/Experiments/UnifiedTrackingModel/ActualProperSplit/MouseV5_2_HQAmp2"),
        "Environment": Path("D:/Experiments/UnifiedTrackingModel/ActualProperSplit/EnvironmentV5_HE1_Reoriented"),
    }

    def _extra_to_dict(self):
        return {
            "cameras": [c.to_dict() for c in self.cameras.values()],
            "groups": [g.to_dict() for g in self.groups.values()],
            "pipelines": [p.to_dict() for p in self.pipelines.values()],
            "placeholders": [v.to_dict() for v in self.placeholders.values()],
            "values": {k: v.to_dict() for k, v in self.values.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data):
        return {
            "cameras": OrderedDict((c["camera_id"], CameraConfig.from_dict(c)) for c in data.get("cameras", [])),
            "groups": OrderedDict((g["recording_id"], GroupConfig.from_dict(g)) for g in data.get("groups", [])),
            "pipelines": OrderedDict((p["camera_id"], PipelineConfig.from_dict(p)) for p in data.get("pipelines", [])),
            "placeholders": OrderedDict((v["variable_id"], VariableConfig.from_dict(v)) for v in data.get("placeholders", [])),
            "values": {k: VariableValue.from_dict(v) for k, v in data.get("values", {}).items()}
        }

    def get_camera_view(self, camera_id: str) -> CameraConfigView:
        camera = self.cameras[camera_id]
        pipeline = self.pipelines[camera_id]
        placeholders = list(self.placeholders.values())

        if camera.recording_id:
            group_id = camera.recording_id
            group_values = self.groups[camera.recording_id].variable_values
        else:
            group_id = camera_id
            group_values = camera.variable_values

        values = {}
        preview_values = {}
        for placeholder in placeholders:
            value = None
            if placeholder.scope == "project":
                value = self.values.get(placeholder.variable_id)
            elif placeholder.scope == "group":
                value = group_values.get(placeholder.variable_id)
            elif placeholder.scope == "camera":
                value = camera.variable_values.get(placeholder.variable_id)
            if value is not None:
                values[placeholder.variable_name] = value.value
                preview_values[placeholder.variable_name] = value.value
            elif placeholder.example_value is not None:
                preview_values[placeholder.variable_name] = placeholder.example_value

        placeholder_context = PlaceholderContext(values)
        preview_placeholder_context = PlaceholderContext(preview_values)
        return CameraConfigView(group_id, self, camera, pipeline, placeholders, placeholder_context, preview_placeholder_context)

    def get_group_view(self, group_id: str) -> GroupConfigView:
        group = self.groups.get(group_id)
        if not group:
            camera = self.cameras.get(group_id)
            if not camera:
                raise ValueError(f"Group or Camera with id {group_id} not found")
            group = self.groups.get("default")
            cameras = [self.get_camera_view(camera.camera_id)]
        else:
            cameras = [self.get_camera_view(camera.camera_id) for camera in self.cameras.values() if camera.recording_id == group_id]

        placeholders = list(self.placeholders.values())
        return GroupConfigView(group_id, group, cameras, placeholders)

    def get_all_group_views(self) -> List[GroupConfigView]:
        group_views = []
        for group_id in self.groups.keys():
            group_views.append(self.get_group_view(group_id))
        ungrouped_cameras = [camera for camera in self.cameras.values() if not camera.recording_id]
        for camera in ungrouped_cameras:
            group_views.append(self.get_group_view(camera.camera_id))
        return group_views