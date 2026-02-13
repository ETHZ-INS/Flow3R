from dataclasses import dataclass, replace
from typing import List

from aaaflow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase
from aaaflow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from aaaflow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class PoseEstimationConfig(PipelineConfigBase):
    video_file: str = "my_video.mp4"
    pose_results_file: str = "pose_results.csv"
    pose_model_folder: str = ""

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "PoseEstimationConfig":
        video_file = PlaceholderFormatter(self.video_file).format(**placeholder_provider.get_placeholder_values())
        pose_results_file = PlaceholderFormatter(self.pose_results_file).format(**placeholder_provider.get_placeholder_values())
        return replace(self, video_file=video_file, pose_results_file=pose_results_file)

    def inputs(self) -> List[str]:
        return ["Video"]
