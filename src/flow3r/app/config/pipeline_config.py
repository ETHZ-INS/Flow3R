import uuid
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional, Type, Self

from flow3r.core.config.abc.config import ConfigBase, ConfigError, ITypedConfig
from flow3r.core.pipeline.abc.pipeline_config import IPipelineConfig
from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider


@dataclass
class PipelineConfig(ConfigBase):
    VERSION = 1

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Pipeline"
    pipeline_type: str = "Record Video"
    sub_configs: Dict[str, Any] = field(default_factory=dict)

    @property
    def active_config(self) -> IPipelineConfig:
        return self.sub_configs[self.pipeline_type]

    def get_sub_config(self, pipeline_type: str) -> Optional[Any]:
        return self.sub_configs.get(pipeline_type)

    def set_sub_config(self, pipeline_type: str, config: Any):
        self.sub_configs[pipeline_type] = config

    def resolve(self, placeholder_provider: IPlaceholderProvider):
        sub_configs = {pipeline_type: config.resolve(placeholder_provider) for pipeline_type, config in self.sub_configs.items()}
        return replace(self, sub_configs=sub_configs)

    def _to_dict_data(self) -> Dict[str, Any]:
        sub_configs = {}
        for source_type, sub_config in self.sub_configs.items():
            sub_configs[source_type] = {
                "type": sub_config.TYPE_ID,
                "data": sub_config.to_dict()
            }

        return {
            "id": self.id,
            "name": self.name,
            "pipeline_type": self.pipeline_type,
            "sub_configs": sub_configs
        }

    @classmethod
    def _from_dict_data(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> Self:
        sub_configs = {}
        for source_type, sub_config_data in data["sub_configs"].items():
            sub_config_type_id = sub_config_data["type"]
            sub_config_data = sub_config_data["data"]
            sub_config_type = type_registry.get(sub_config_type_id)

            if sub_config_type is None:
                raise ConfigError(f"Unknown config type: {sub_config_type_id}")

            sub_configs[source_type] = sub_config_type.from_dict(sub_config_data, type_registry)

        return cls(
            id=data["id"],
            name=data["name"],
            pipeline_type=data["pipeline_type"],
            sub_configs=sub_configs,
        )
