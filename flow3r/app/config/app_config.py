from dataclasses import dataclass, field
from typing import OrderedDict, Dict, Any, Self, Type

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.config.pipeline_config import PipelineConfig
from flow3r.app.config.placeholder_config import PlaceholderConfig
from flow3r.core.config.abc.config import ConfigBase, ITypedConfig, ConfigError
from flow3r.core.settings import KeyPath
from flow3r.app.config.source_config import SourceConfig


@dataclass
class AppConfig(ConfigBase):
    settings: Dict[KeyPath, Any] = field(default_factory=dict)

    sources: OrderedDict[str, SourceConfig] = field(default_factory=OrderedDict)
    groups: OrderedDict[str, GroupConfig] = field(default_factory=OrderedDict)
    implicit_groups: OrderedDict[str, GroupConfig] = field(default_factory=OrderedDict)
    pipelines: OrderedDict[str, PipelineConfig] = field(default_factory=OrderedDict)

    placeholders: Dict[str, PlaceholderConfig] = field(default_factory=dict)
    global_placeholder_values: Dict[str, str] = field(default_factory=dict)
    group_placeholder_values: Dict[str, Dict[str, str]] = field(default_factory=dict)

    @property
    def all_groups(self) -> Dict[str, GroupConfig]:
        return self.groups | self.implicit_groups

    @property
    def global_placeholder_values_dict(self) -> Dict[str, str]:
        constant_values = {
            placeholder_config.name: placeholder_config.constant_value
            for placeholder_config in self.placeholders.values()
            if placeholder_config.is_constant
        }

        return constant_values | {
            placeholder_config.name: self.global_placeholder_values[placeholder_config.id]
            for placeholder_config in self.placeholders.values()
            if placeholder_config.is_global and placeholder_config.id in self.global_placeholder_values
        }

    def _to_dict_data(self) -> Dict[str, Any]:
        settings = []
        for key_path, value in self.settings.items():
            settings.append({
                "key": list(key_path),
                "type": value.TYPE_ID,
                "data": value.to_dict()
            })

        sources = {source_id: source.to_dict() for source_id, source in self.sources.items()}
        groups = {group_id: group.to_dict() for group_id, group in self.groups.items()}
        implicit_groups = {group_id: group.to_dict() for group_id, group in self.implicit_groups.items()}
        pipelines = {pipeline_id: pipeline.to_dict() for pipeline_id, pipeline in self.pipelines.items()}
        placeholders = {placeholder_id: placeholder.to_dict() for placeholder_id, placeholder in self.placeholders.items()}

        return {
            "settings": settings,
            "sources": sources,
            "groups": groups,
            "implicit_groups": implicit_groups,
            "pipelines": pipelines,
            "placeholders": placeholders,
        }

    @classmethod
    def _from_dict_data(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> Self:
        settings = {}
        for setting_data in data["settings"]:
            key_path = tuple(setting_data["key"])
            setting_type_id = setting_data["type"]
            setting_data = setting_data["data"]
            setting_type = type_registry.get(setting_type_id)

            if setting_type is None:
                raise ConfigError(f"Unknown config type: {setting_type_id}")

            settings[key_path] = setting_type.from_dict(setting_data, type_registry)

        return cls(
            settings=settings,
            sources=OrderedDict({source_id: SourceConfig.from_dict(source_data, type_registry) for source_id, source_data in data["sources"].items()}),
            groups=OrderedDict({group_id: GroupConfig.from_dict(group_data, type_registry) for group_id, group_data in data["groups"].items()}),
            implicit_groups=OrderedDict({group_id: GroupConfig.from_dict(group_data, type_registry) for group_id, group_data in data["implicit_groups"].items()}),
            pipelines=OrderedDict({pipeline_id: PipelineConfig.from_dict(pipeline_data, type_registry) for pipeline_id, pipeline_data in data["pipelines"].items()}),
            placeholders=OrderedDict({placeholder_id: PlaceholderConfig.from_dict(placeholder_data, type_registry) for placeholder_id, placeholder_data in data["placeholders"].items()}),
        )
