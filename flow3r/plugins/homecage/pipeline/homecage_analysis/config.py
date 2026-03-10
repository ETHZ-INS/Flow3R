from dataclasses import dataclass, replace
from typing import List, Set, Tuple

from flow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase
from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from flow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class HomecageAnalysisConfig(PipelineConfigBase):
    use_3d_camera: bool = False
    top_video_file: str = "top_video.mp4"
    offset_video_file: str = "offset_video.mp4"
    top_pose_results_file: str = "top_poses.csv"
    offset_pose_results_file: str = "offset_poses.csv"
    calibration_file: str = "calibration.json"
    live_results_input_folder: str = "live_results_input"
    mouse_pose_model_id: str = None
    environment_pose_model_id: str = None

    @property
    def settings_dependencies(self) -> Set[Tuple[str, ...]]:
        return {("pose_estimation", "models")}

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "HomecageAnalysisConfig":
        top_video_file = PlaceholderFormatter(self.top_video_file).format(**placeholder_provider.get_placeholder_values())
        offset_video_file = PlaceholderFormatter(self.offset_video_file).format(**placeholder_provider.get_placeholder_values())
        top_pose_results_file = PlaceholderFormatter(self.top_pose_results_file).format(**placeholder_provider.get_placeholder_values())
        offset_pose_results_file = PlaceholderFormatter(self.offset_pose_results_file).format(**placeholder_provider.get_placeholder_values())
        return replace(self, top_video_file=top_video_file, offset_video_file=offset_video_file, top_pose_results_file=top_pose_results_file, offset_pose_results_file=offset_pose_results_file)

    @property
    def inputs(self) -> List[str]:
        if self.use_3d_camera:
            return ["Top 3D Camera"]
        return ["Top Video", "Offset Video"]
