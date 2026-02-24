from dataclasses import dataclass
from typing import Tuple


@dataclass
class VideoFormat:
    size: Tuple[int, int]
    fps: float
    fmt: str = "bgr24"
