from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioFileSourceConfig:
    file_path: Optional[str] = None
