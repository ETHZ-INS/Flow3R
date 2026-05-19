from dataclasses import dataclass
from typing import ClassVar

from flow3r.core.config.abc.config import ITypedConfig, ConfigBase

ISettingsConfig = ITypedConfig


@dataclass
class SettingsBase(ConfigBase, ITypedConfig):
    TYPE_ID: ClassVar[str]
