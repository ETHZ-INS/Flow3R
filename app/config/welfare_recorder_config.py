from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Dict, List, Tuple

from app.config.camera_config import CameraConfig
from app.config.config_base import ConfigBase
from app.config.pipeline_config import PipelineConfig
from app.config.group_config import GroupConfig
from app.config.pose_estimation_model_config import PoseEstimationModelConfig, PoseEstimationPresetConfig
from app.config.variable_config import VariableValue, VariableConfig
from app.placeholder_context import PlaceholderContext


BUILTIN_POSE_MODELS = {
    m.id: m for m in [
        PoseEstimationModelConfig(id="bohaceklab_mouse_v5_2", name="BohacekLab Mouse V5.2", type="yolo_3r_hub", folder=Path("D:/Experiments/UnifiedTrackingModel/ActualProperSplit/MouseV5_2_HQAmp2")),
        PoseEstimationModelConfig(id="bohaceklab_environment_v5_2", name="BohacekLab Environment V5.2", type="yolo_3r_hub", folder=Path("D:/Experiments/UnifiedTrackingModel/ActualProperSplit/EnvironmentV5_HE1_Reoriented")),
    ]
}

BUILTIN_POSE_PRESETS = {
    p.id: p for p in [
        PoseEstimationPresetConfig(id="bohaceklab_epm", name="BohacekLab EPM", models=["bohaceklab_mouse_v5_2", "bohaceklab_environment_v5_2"]),
    ]
}


@dataclass
class CameraConfigView:
    group_id: str
    project: "WelfareRecorderConfig"
    camera: CameraConfig
    pipeline: PipelineConfig
    placeholders: List[VariableConfig]
    placeholder_context: PlaceholderContext
    preview_placeholder_context: PlaceholderContext

    @property
    def error(self) -> Tuple[List[str], str] | None:
        configs = [self.camera, self.pipeline] + self.placeholders
        for config in configs:
            error = config.error
            if error:
                return error
        return None

    def get_required_placeholders(self) -> set[str]:
        required_placeholders = self.pipeline.get_required_placeholders()
        for placeholder in list(required_placeholders):
            dependencies = self.placeholder_context.dependencies(placeholder)
            required_placeholders.update(dependencies)
        return required_placeholders

    def get_placeholder_context(self, preview: bool = False) -> PlaceholderContext:
        values = {}
        values["camera_name"] = self.camera.camera_name
        for placeholder in self.placeholders:
            if placeholder.is_system:
                continue

            value = None
            if placeholder.scope == "project":
                value = self.project.values.get(placeholder.variable_id)
            elif placeholder.scope == "group":
                if self.camera.group_id:
                    group = self.project.groups.get(self.camera.group_id)
                    if group:
                        value = group.variable_values.get(placeholder.variable_id)
                else:
                    value = self.camera.variable_values.get(placeholder.variable_id)
            elif placeholder.scope == "camera":
                value = self.camera.variable_values.get(placeholder.variable_id)
            if value is not None:
                values[placeholder.variable_name] = value.value
            elif preview and placeholder.example_value is not None:
                values[placeholder.variable_name] = placeholder.example_value
        return PlaceholderContext(values)


@dataclass
class GroupConfigView:
    group_id: str
    project: "WelfareRecorderConfig"
    group: GroupConfig
    cameras: List[CameraConfigView]
    placeholders: List[VariableConfig]

    @property
    def error(self) -> Tuple[List[str], str] | None:
        configs = [self.group] + self.cameras + self.placeholders
        for config in configs:
            error = config.error
            if error:
                return error
        return None


@dataclass
class PipelineConfigView:
    project: "WelfareRecorderConfig"
    pipeline: PipelineConfig
    cameras: List[CameraConfigView]
    placeholders: List[VariableConfig]


@dataclass
class WelfareRecorderConfig(ConfigBase):
    cameras: OrderedDict[str, CameraConfig] = field(default_factory=OrderedDict)
    groups: OrderedDict[str, GroupConfig] = field(default_factory=lambda: OrderedDict({'default': GroupConfig(group_id='default', recording_name='Default (Individual)')}))
    pipelines: OrderedDict[str, PipelineConfig] = field(default_factory=lambda: OrderedDict({'default': PipelineConfig(pipeline_id='default', pipeline_name='Default')}))
    placeholders: OrderedDict[str, VariableConfig] = field(default_factory=lambda: OrderedDict({'camera_name': VariableConfig(variable_id='camera_name', variable_name='camera_name', variable_label="Camera Name", variable_type="text", is_system=True, scope='camera', description='Name of the camera', example_value='Camera1')}))

    pose_models: OrderedDict[str, PoseEstimationModelConfig] = field(default_factory=lambda: OrderedDict(deepcopy(BUILTIN_POSE_MODELS)))
    pose_estimation_presets: OrderedDict[str, PoseEstimationPresetConfig] = field(default_factory=lambda: OrderedDict(deepcopy(BUILTIN_POSE_PRESETS)))

    values: Dict[str, VariableValue] = field(default_factory=dict)

    @property
    def error(self) -> Tuple[List[str], str] | None:
        configs = []
        configs += list(self.cameras.values())
        configs += list(self.groups.values())
        configs += list(self.pipelines.values())
        configs += list(self.placeholders.values())
        configs += list(self.pose_models.values())
        configs += list(self.pose_estimation_presets.values())
        for config in configs:
            error = config.error
            if error:
                return error
        return None

    def _extra_to_dict(self):
        return {
            "cameras": [c.to_dict() for c in self.cameras.values()],
            "groups": [g.to_dict() for g in self.groups.values()],
            "pipelines": [p.to_dict() for p in self.pipelines.values()],
            "placeholders": [v.to_dict() for v in self.placeholders.values()],
            "pose_models": [m.to_dict() for m in self.pose_models.values()],
            "pose_estimation_presets": [p.to_dict() for p in self.pose_estimation_presets.values()],
            "values": {k: v.to_dict() for k, v in self.values.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data):
        return {
            "cameras": OrderedDict((c["camera_id"], CameraConfig.from_dict(c)) for c in data.get("cameras", [])),
            "groups": OrderedDict((g["group_id"], GroupConfig.from_dict(g)) for g in data.get("groups", [])),
            "pipelines": OrderedDict((p["pipeline_id"], PipelineConfig.from_dict(p)) for p in data.get("pipelines", [])),
            "placeholders": OrderedDict((v["variable_id"], VariableConfig.from_dict(v)) for v in data.get("placeholders", [])),
            "pose_models": OrderedDict((m["id"], PoseEstimationModelConfig.from_dict(m)) for m in data.get("pose_models", [])),
            "pose_estimation_presets": OrderedDict((p["id"], PoseEstimationPresetConfig.from_dict(p)) for p in data.get("pose_estimation_presets", [])),
            "values": {k: VariableValue.from_dict(v) for k, v in data.get("values", {}).items()}
        }

    def get_camera_view(self, camera_id: str) -> CameraConfigView:
        camera = self.cameras[camera_id]
        if camera.pipeline_id:
            pipeline = self.pipelines[camera.pipeline_id]
        else:
            pipeline = self.pipelines.get("default")
        placeholders = list(self.placeholders.values())

        if camera.group_id:
            group_id = camera.group_id
            group_values = self.groups[camera.group_id].variable_values
        else:
            group_id = camera_id
            group_values = camera.variable_values

        values = {}
        preview_values = {}
        values["camera_name"] = camera.camera_name
        preview_values["camera_name"] = camera.camera_name
        for placeholder in placeholders:
            if placeholder.is_system:
                continue
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
            cameras = [self.get_camera_view(camera.camera_id) for camera in self.cameras.values() if camera.activated and camera.group_id == group_id]

        placeholders = list(self.placeholders.values())
        return GroupConfigView(group_id, self, group, cameras, placeholders)

    def get_all_group_views(self) -> List[GroupConfigView]:
        group_views = []
        for group_id in self.groups.keys():
            group_views.append(self.get_group_view(group_id))
        for camera in self.cameras.values():
            if not camera.group_id:
                group_views.append(self.get_group_view(camera.camera_id))
        return group_views

    def get_pipeline_view(self, pipeline_id: str) -> PipelineConfigView:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline with id {pipeline_id} not found")

        if pipeline.is_default:
            cameras = [self.get_camera_view(camera.camera_id) for camera in self.cameras.values() if camera.pipeline_id is None or camera.pipeline_id == "default"]
        else:
            cameras = [self.get_camera_view(camera.camera_id) for camera in self.cameras.values() if camera.pipeline_id == pipeline_id]

        placeholders = list(self.placeholders.values())
        return PipelineConfigView(self, pipeline, cameras, placeholders)

    def get_all_pipeline_views(self) -> List[PipelineConfigView]:
        pipeline_views = []
        for pipeline_id in self.pipelines.keys():
            pipeline_views.append(self.get_pipeline_view(pipeline_id))
        return pipeline_views

    def get_placeholder_context(self, preview: bool = False) -> PlaceholderContext:
        values = {}
        for placeholder in self.placeholders.values():
            value = None
            if placeholder.scope == "project":
                value = self.values.get(placeholder.variable_id)
            if value is not None:
                values[placeholder.variable_name] = value.value
            elif preview and placeholder.example_value is not None:
                values[placeholder.variable_name] = placeholder.example_value
        return PlaceholderContext(values)
