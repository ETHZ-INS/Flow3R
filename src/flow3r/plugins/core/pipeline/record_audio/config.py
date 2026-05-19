from dataclasses import dataclass, replace
from typing import ClassVar, List, Self

from flow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase
from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from flow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class RecordAudioConfig(PipelineConfigBase):
    TYPE_ID: ClassVar[str] = "core.pipeline.record_audio"
    VERSION: ClassVar[int] = 1

    audio_file: str = "my_audio.wav"

    @property
    def inputs(self) -> List[str]:
        return ["Audio"]

    @property
    def files(self) -> List[str]:
        return [self.audio_file]

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> Self:
        audio_file = PlaceholderFormatter(self.audio_file).format(**placeholder_provider.get_placeholder_values())
        return replace(self, audio_file=audio_file)
