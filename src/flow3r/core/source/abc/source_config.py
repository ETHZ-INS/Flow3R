from dataclasses import dataclass
from typing import ClassVar

from flow3r.core.config.abc.config import ITypedConfig, ConfigBase

ISourceConfig = ITypedConfig


@dataclass
class SourceConfigBase(ConfigBase, ISourceConfig):
    TYPE_ID: ClassVar[str]
