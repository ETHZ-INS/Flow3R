from dataclasses import dataclass, field
from typing import OrderedDict, Dict, Any

from aaaflow3r.app.config.group_config import GroupConfig
from aaaflow3r.core.pipeline.pipeline_config import PipelineConfig
from aaaflow3r.core.settings import KeyPath
from aaaflow3r.core.source.source_config import SourceConfig


@dataclass
class AppConfig:
    settings: Dict[KeyPath, Any] = field(default_factory=dict)

    sources: OrderedDict[str, SourceConfig] = field(default_factory=OrderedDict)
    groups: OrderedDict[str, GroupConfig] = field(default_factory=OrderedDict)
    implicit_groups: OrderedDict[str, GroupConfig] = field(default_factory=OrderedDict)
    pipelines: OrderedDict[str, PipelineConfig] = field(default_factory=OrderedDict)
