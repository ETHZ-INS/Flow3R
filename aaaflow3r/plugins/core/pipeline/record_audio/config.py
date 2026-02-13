from dataclasses import dataclass
from typing import List

from aaaflow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase


@dataclass
class RecordAudioConfig(PipelineConfigBase):
    audio_file: str = "my_audio.wav"

    def inputs(self) -> List[str]:
        return ["Audio"]
