from dataclasses import dataclass, field
from typing import OrderedDict

from aaaflow3r.app.config.group_config import GroupConfig
from aaaflow3r.app.config.recording_config import RecordingConfig
from aaaflow3r.core.pipeline.pipeline_config import PipelineConfig
from aaaflow3r.core.source.source_config import SourceConfig


@dataclass
class AppConfig:
    sources: OrderedDict[str, SourceConfig] = field(default_factory=OrderedDict)
    groups: OrderedDict[str, GroupConfig] = field(default_factory=OrderedDict)
    implicit_groups: OrderedDict[str, GroupConfig] = field(default_factory=OrderedDict)
    pipelines: OrderedDict[str, PipelineConfig] = field(default_factory=OrderedDict)

    default_recording_config: RecordingConfig = field(default_factory=RecordingConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)