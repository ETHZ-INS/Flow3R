from dataclasses import dataclass, replace
from typing import List, Set, Tuple

from flow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase
from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from flow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class HomecageAnalysisConfig(PipelineConfigBase):
    TYPE_ID = "homecage.pipeline.homecage_analysis"
    VERSION = 1

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
            return ["Top 3D Video"]
        return ["Top Video", "Offset Video"]

    @property
    def optional_inputs(self) -> List[str]:
        return []

    @property
    def files(self) -> List[str]:
        # TODO: Maybe return a few example files that would be created in the live_results_input_folder folder?
        return [self.top_video_file, self.offset_video_file, self.top_pose_results_file, self.offset_pose_results_file]
