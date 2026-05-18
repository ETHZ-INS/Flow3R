from dataclasses import dataclass, replace
from typing import List, ClassVar, Dict

from flow3r.core.pipeline.abc.pipeline_config import PipelineConfigBase
from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider
from flow3r.core.placeholder.placeholder_formatter import PlaceholderFormatter


@dataclass
class RecordVideoConfig(PipelineConfigBase):
    TYPE_ID: ClassVar[str] = "core.pipeline.record_video"
    VERSION: ClassVar[int] = 1

    QUALITY_CHOICES: ClassVar[Dict[str, str]] = {
        "low": "Low",
        "medium": "Medium",
        "high": "High"
    }

    video_file: str = "my_video.mp4"
    video_quality: str = "medium"

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "RecordVideoConfig":
        video_file = PlaceholderFormatter(self.video_file).format(**placeholder_provider.get_placeholder_values())
        return replace(self, video_file=video_file)

    @property
    def inputs(self) -> List[str]:
        return ["Video"]

    @property
    def files(self) -> List[str]:
        return [self.video_file]
