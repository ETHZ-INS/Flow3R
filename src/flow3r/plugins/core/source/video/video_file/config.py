from dataclasses import dataclass
from typing import ClassVar, Optional

from flow3r.core.source.abc.source_config import SourceConfigBase


@dataclass
class VideoFileSourceConfig(SourceConfigBase):
    TYPE_ID: ClassVar[str] = "core.source.video.video_file"
    VERSION: ClassVar[int] = 1

    file_path: Optional[str] = None
    grayscale: bool = False
    loop: bool = False
