import uuid
from dataclasses import dataclass, field
from typing import List, Tuple

from app.config.config_base import ConfigBase
from app.config.pose_estimation_config import PoseEstimationConfig
from app.config.save_video_config import SaveVideoConfig


@dataclass
class PipelineConfig(ConfigBase):
    pipeline_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    pipeline_name: str = "New Pipeline"

    save_video: bool = True
    save_video_config: SaveVideoConfig = field(default_factory=SaveVideoConfig)

    pose_estimation: bool = False
    pose_estimation_config: PoseEstimationConfig = field(default_factory=PoseEstimationConfig)

    @property
    def is_default(self) -> bool:
        return self.pipeline_id == 'default'

    @property
    def location(self) -> List[str]:
        return ["pipeline", self.pipeline_id]

    @property
    def error(self) -> Tuple[List[str], str] | None:
        if not self.pipeline_id:
            return self.location, "Pipeline ID is empty."
        if not self.pipeline_name:
            return self.location, "Pipeline name is empty."
        if self.save_video:
            error = self.save_video_config.error
            if error:
                return self.location + ["save_video"], error
        if self.pose_estimation:
            error = self.pose_estimation_config.error
            if error:
                return self.location + ["pose_estimation"], error
        return None


    def _extra_to_dict(self) -> dict:
        return {
            'pipeline_id': self.pipeline_id,
            'pipeline_name': self.pipeline_name,
            'save_video': self.save_video,
            'save_video_config': self.save_video_config.to_dict(),
            'pose_estimation': self.pose_estimation,
            'pose_estimation_config': self.pose_estimation_config.to_dict()
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "pipeline_id": data["pipeline_id"],
            "pipeline_name": data.get("pipeline_name", "New Pipeline"),
            "save_video": data.get('save_video', True),
            "save_video_config": SaveVideoConfig.from_dict(data.get('save_video_config', {})),
            "pose_estimation": data.get('pose_estimation', False),
            "pose_estimation_config": PoseEstimationConfig.from_dict(data.get('pose_estimation_config', {}))
        }

    def get_required_placeholders(self) -> set:
        vars = set()
        if self.save_video:
            vars.update(self.save_video_config.get_required_placeholders())
        if self.pose_estimation:
            vars.update(self.pose_estimation_config.get_required_variables())
        return vars
