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
    VERSION = 1

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

    def group_placeholder_values_dict(self, group_id: str) -> Dict[str, str]:
        """Return placeholder name→value mapping for a specific group,
        including global values so callers get a complete substitution dict."""
        group_values = self.group_placeholder_values.get(group_id, {})
        return self.global_placeholder_values_dict | {
            placeholder_config.name: group_values[placeholder_config.id]
            for placeholder_config in self.placeholders.values()
            if not placeholder_config.is_global and placeholder_config.id in group_values
        }

    def _to_dict_data(self) -> Dict[str, Any]:
        settings = []
        for key_path, value in self.settings.items():
            settings.append({
                "key": list(key_path),
                "type": value.TYPE_ID,
                "data": value.to_dict()
            })

        # Only persist placeholder values that are marked as project-persistent
        project_placeholder_ids = {
            p.id for p in self.placeholders.values()
            if p.persistence == 'project'
        }
        persistent_global_values = {
            k: v for k, v in self.global_placeholder_values.items()
            if k in project_placeholder_ids
        }
        persistent_group_values = {
            group_id: {
                k: v for k, v in values.items()
                if k in project_placeholder_ids
            }
            for group_id, values in self.group_placeholder_values.items()
        }

        return {
            "settings": settings,
            "sources": [v.to_dict() for k, v in self.sources.items()],
            "groups": [v.to_dict() for k, v in self.groups.items()],
            "implicit_groups": [v.to_dict() for k, v in self.implicit_groups.items()],
            "pipelines": [v.to_dict() for k, v in self.pipelines.items()],
            "placeholders": [v.to_dict() for k, v in self.placeholders.items()],
            "global_placeholder_values": persistent_global_values,
            "group_placeholder_values": persistent_group_values,
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

        sources = [SourceConfig.from_dict(source_data, type_registry) for source_data in data["sources"]]
        groups = [GroupConfig.from_dict(group_data, type_registry) for group_data in data["groups"]]
        implicit_groups = [GroupConfig.from_dict(group_data, type_registry) for group_data in data["implicit_groups"]]
        pipelines = [PipelineConfig.from_dict(pipeline_data, type_registry) for pipeline_data in data["pipelines"]]
        placeholders = [PlaceholderConfig.from_dict(placeholder_data, type_registry) for placeholder_data in data["placeholders"]]

        return cls(
            settings=settings,
            sources=OrderedDict(((source.id, source) for source in sources)),
            groups=OrderedDict(((group.id, group) for group in groups)),
            implicit_groups=OrderedDict(((group.id, group) for group in implicit_groups)),
            pipelines=OrderedDict(((pipeline.id, pipeline) for pipeline in pipelines)),
            placeholders={placeholder.id: placeholder for placeholder in placeholders},
            global_placeholder_values=data.get("global_placeholder_values", {}),
            group_placeholder_values=data.get("group_placeholder_values", {}),
        )
