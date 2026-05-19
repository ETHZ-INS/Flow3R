from dataclasses import dataclass
from pathlib import Path
from typing import List

from py3r.media.types import FrameMeta

from flow3r.plugins.core.typing.video import VideoFormat


@dataclass
class VideoSegmentFormat:
    video_format: VideoFormat
    segment_length_seconds: float


@dataclass
class VideoSegment:
    file_path: Path
    segment_index: int
    frame_metas: List[FrameMeta]
