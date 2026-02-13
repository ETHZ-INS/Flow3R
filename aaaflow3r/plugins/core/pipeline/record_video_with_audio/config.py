from dataclasses import dataclass

from aaaflow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase
from aaaflow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from aaaflow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class RecordVideoWithAudioConfig(PipelineConfigBase):
    video_file: str = "my_video.mp4"

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "RecordVideoWithAudioConfig":
        video_file = PlaceholderFormatter(self.video_file).format(**placeholder_provider.get_placeholder_values())
        return RecordVideoWithAudioConfig(video_file=video_file)

    def inputs(self) -> list[str]:
        return ["Video", "Audio"]
