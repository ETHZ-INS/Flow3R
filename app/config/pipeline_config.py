from dataclasses import dataclass, field
from typing import Dict

from app.config.config_base import ConfigBase
from app.config.pose_estimation_config import PoseEstimationConfig
from app.config.save_video_config import SaveVideoConfig


@dataclass
class PipelineConfig(ConfigBase):
    camera_id: str
    save_video: bool = True
    save_video_config: SaveVideoConfig = field(default_factory=SaveVideoConfig)

    pose_estimation: bool = False
    pose_estimation_config: PoseEstimationConfig = field(default_factory=PoseEstimationConfig)

    def _extra_to_dict(self) -> dict:
        return {
            'camera_id': self.camera_id,
            'save_video': self.save_video,
            'save_video_config': self.save_video_config.to_dict(),
            'pose_estimation': self.pose_estimation,
            'pose_estimation_config': self.pose_estimation_config.to_dict()
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "camera_id": data["camera_id"],
            "save_video": data.get('save_video', True),
            "save_video_config": SaveVideoConfig.from_dict(data.get('save_video_config', {})),
            "pose_estimation": data.get('pose_estimation', False),
            "pose_estimation_config": PoseEstimationConfig.from_dict(data.get('pose_estimation_config', {}))
        }

    def get_required_placeholders(self) -> set:
        vars = set()
        if self.save_video:
            vars.update(self.save_video_config.get_required_variables())
        if self.pose_estimation:
            vars.update(self.pose_estimation_config.get_required_variables())
        return vars


@dataclass
class PipelineConfigList(ConfigBase):
    pipelines: Dict[str, PipelineConfig] = field(default_factory=dict)

    def _extra_to_dict(self):
        return {
            "pipelines": {camera_id: pipeline.to_dict() for camera_id, pipeline in self.pipelines.items()}
        }

    @classmethod
    def _extra_from_dict(cls, data: dict):
        return {
            "pipelines": {camera_id: PipelineConfig.from_dict(pipeline_data) for camera_id, pipeline_data in data.get("pipelines", {}).items()}
        }

    def get(self, camera_id: str) -> PipelineConfig:
        return self.pipelines.get(camera_id)

    def set(self, config: PipelineConfig):
        self.pipelines[config.camera_id] = config

    def remove(self, camera_id: str):
        if camera_id in self.pipelines:
            del self.pipelines[camera_id]