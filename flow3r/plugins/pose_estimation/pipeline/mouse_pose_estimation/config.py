from dataclasses import dataclass, replace
from typing import List, Set, Tuple

from flow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase
from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from flow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class MousePoseEstimationConfig(PipelineConfigBase):
    video_file: str = "my_video.mp4"
    pose_results_file: str = "pose_results.csv"
    mouse_pose_model_id: str = None
    env_pose_model_id: str = None

    @property
    def settings_dependencies(self) -> Set[Tuple[str, ...]]:
        return {("pose_estimation", "models")}

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "MousePoseEstimationConfig":
        video_file = PlaceholderFormatter(self.video_file).format(**placeholder_provider.get_placeholder_values())
        pose_results_file = PlaceholderFormatter(self.pose_results_file).format(**placeholder_provider.get_placeholder_values())
        return replace(self, video_file=video_file, pose_results_file=pose_results_file)

    def inputs(self) -> List[str]:
        return ["Video"]
