from dataclasses import dataclass
from pathlib import Path

from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


@dataclass
class PoseSegmentFormat:
    pose_format: PoseFormat


@dataclass
class PoseSegment:
    file_path: Path
    segment_index: int
