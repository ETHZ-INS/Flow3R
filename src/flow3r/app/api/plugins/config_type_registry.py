from typing import Type, Dict

from flow3r.core.api.plugins.config_type_registry import IConfigTypeRegistry
from flow3r.core.config.abc.config import IConfig, ITypedConfig


class ConfigTypeRegistry(IConfigTypeRegistry):
    def __init__(self):
        self._config_types: Dict[str, Type[ITypedConfig]] = {}

    def register(self, config_type_id: str, config_type: Type[ITypedConfig]):
        self._config_types[config_type_id] = config_type

    @property
    def config_types(self) -> Dict[str, Type[ITypedConfig]]:
        return self._config_types
