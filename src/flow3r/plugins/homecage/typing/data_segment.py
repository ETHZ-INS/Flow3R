from dataclasses import dataclass
from pathlib import Path

from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


@dataclass
class HomecageDataSegmentFormat:
    video_format: VideoFormat
    pose_format: PoseFormat
    segment_length_seconds: float


@dataclass
class TopCameraDataSegment:
    video_file: Path
    visualization_file: Path
    pose_file: Path


@dataclass
class TopDataSegment:
    left: TopCameraDataSegment
    right: TopCameraDataSegment
    calibration_file: Path


@dataclass
class HomecageDataSegment:
    segment_index: int
    top_data_segment: TopDataSegment
