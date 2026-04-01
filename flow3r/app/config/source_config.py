import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type, Self

from flow3r.core.config.abc.config import ConfigBase, ConfigError, ITypedConfig
from flow3r.core.source.abc.source_config import ISourceConfig


@dataclass
class SourceConfig(ConfigBase):
    VERSION = 1

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Source"
    group_id: Optional[str] = None
    active: bool = True
    source_type: str = "Webcam"
    sub_configs: Dict[str, ISourceConfig] = field(default_factory=dict)

    @property
    def active_config(self) -> Any:
        return self.sub_configs[self.source_type]

    def get_sub_config(self, source_type: str) -> Optional[Any]:
        return self.sub_configs.get(source_type)

    def set_sub_config(self, source_type: str, config: Any):
        self.sub_configs[source_type] = config

    @property
    def implicit_group_id(self) -> str:
        return self.group_id if self.group_id is not None else self.id

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
            "group_id": self.group_id,
            "active": self.active,
            "source_type": self.source_type,
            "sub_configs": sub_configs,
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
            group_id=data["group_id"],
            active=data["active"],
            source_type=data["source_type"],
            sub_configs=sub_configs,
        )
