from typing import Protocol, Type

from flow3r.core.config.abc.config import ITypedConfig


class IConfigTypeRegistry(Protocol):
    def register(self, config_type_id: str, config_type: Type[ITypedConfig]): ...
