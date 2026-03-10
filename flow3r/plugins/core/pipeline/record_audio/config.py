from dataclasses import dataclass
from typing import List

from flow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase


@dataclass
class RecordAudioConfig(PipelineConfigBase):
    audio_file: str = "my_audio.wav"

    @property
    def inputs(self) -> List[str]:
        return ["Audio"]
