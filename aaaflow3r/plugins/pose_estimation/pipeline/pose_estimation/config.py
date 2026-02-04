from dataclasses import dataclass


@dataclass
class PoseEstimationConfig:
    video_file: str = "my_video.mp4"
    pose_results_file: str = "pose_results.csv"
    pose_model_folder: str = ""
