from dataclasses import dataclass
from typing import Optional


@dataclass
class VideoFileSourceConfig:
    file_path: Optional[str] = None
    grayscale: bool = False
    loop: bool = False
