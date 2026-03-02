from dataclasses import dataclass, field
from typing import OrderedDict, Dict, Any

from flow3r.app.config.group_config import GroupConfig
from flow3r.core.pipeline.pipeline_config import PipelineConfig
from flow3r.core.settings import KeyPath
from flow3r.core.source.source_config import SourceConfig


@dataclass
class AppConfig:
    settings: Dict[KeyPath, Any] = field(default_factory=dict)

    sources: OrderedDict[str, SourceConfig] = field(default_factory=OrderedDict)
    groups: OrderedDict[str, GroupConfig] = field(default_factory=OrderedDict)
    implicit_groups: OrderedDict[str, GroupConfig] = field(default_factory=OrderedDict)
    pipelines: OrderedDict[str, PipelineConfig] = field(default_factory=OrderedDict)

    @property
    def all_groups(self) -> Dict[str, GroupConfig]:
        return self.groups | self.implicit_groups
