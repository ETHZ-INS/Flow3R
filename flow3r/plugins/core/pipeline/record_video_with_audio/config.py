from dataclasses import dataclass

from flow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase
from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from flow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class RecordVideoWithAudioConfig(PipelineConfigBase):
    TYPE_ID = "core.pipeline.record_video_with_audio"
    VERSION = 1

    video_file: str = "my_video.mp4"

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "RecordVideoWithAudioConfig":
        video_file = PlaceholderFormatter(self.video_file).format(**placeholder_provider.get_placeholder_values())
        return RecordVideoWithAudioConfig(video_file=video_file)

    @property
    def inputs(self) -> list[str]:
        return ["Video", "Audio"]

    @property
    def files(self) -> list[str]:
        return [self.video_file]
