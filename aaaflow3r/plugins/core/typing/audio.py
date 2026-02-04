from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class AudioFormat:
    sample_rate: int
    channels: int
    sample_format: Literal["f32", "s16"]
    chunk_size: int


@dataclass(frozen=True)
class AudioChunk:
    timestamp: float              # timestamp of first sample
    samples: np.ndarray         # shape (chunk_size, channels)
