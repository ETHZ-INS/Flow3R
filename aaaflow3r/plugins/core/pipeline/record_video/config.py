from dataclasses import dataclass
from typing import Self

from aaaflow3r.core.pipeline.abc.pipeline_config import PipelineConfig
from aaaflow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from aaaflow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class RecordVideoConfig(PipelineConfig):
    video_file: str = "my_video.mp4"

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> Self:
        video_file = PlaceholderFormatter(self.video_file).format(**placeholder_provider.get_placeholder_values())
        return RecordVideoConfig(video_file=video_file)
