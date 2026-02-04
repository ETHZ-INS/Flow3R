from dataclasses import dataclass

from aaaflow3r.plugins.core.typing.video import VideoFormat


@dataclass
class VideoSegmentFormat:
    video_format: VideoFormat
    segment_length_seconds: float
