from dataclasses import dataclass
from typing import Optional

from flow3r.core.source.abc.source_config import SourceConfigBase


@dataclass
class VideoFileSourceConfig(SourceConfigBase):
    TYPE_ID = "core.source.video.video_file"
    VERSION = 1

    file_path: Optional[str] = None
    grayscale: bool = False
    loop: bool = False
