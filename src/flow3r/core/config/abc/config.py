from abc import ABC
from dataclasses import dataclass
from typing import Protocol, Self, ClassVar, Any, Type, Dict


class ConfigError(Exception):
    pass


class ConfigTypeMismatchError(ConfigError):
    pass


class ConfigVersionError(ConfigError):
    pass


class IConfig(Protocol):
    @classmethod
    def from_dict(cls, data: Dict[str, Any], type_registry: Dict[str, Type["ITypedConfig"]]) -> Self: ...
    def to_dict(self) -> Dict[str, Any]: ...


class ITypedConfig(IConfig, Protocol):
    TYPE_ID: ClassVar[str]


@dataclass
class ConfigBase(ABC, IConfig):
    VERSION: ClassVar[int] = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "data": self._to_dict_data(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> Self:
        version = data.get("version")
        inner_data = data.get("data")

        if not isinstance(version, int):
            raise ConfigVersionError(f"Invalid config version: {version!r}")

        if not isinstance(inner_data, dict):
            raise ConfigError(f"Invalid config data")

        if version != cls.VERSION:
            assert isinstance(version, int)
            inner_data = cls._migrate_data(inner_data, from_version=version)

        return cls._from_dict_data(inner_data, type_registry)

    def _to_dict_data(self) -> Dict[str, Any]:
        return self.__dict__

    @classmethod
    def _from_dict_data(cls, data: Dict[str, Any], type_registry: Dict[str, Type[ITypedConfig]]) -> Self:
        return cls(**data)

    @classmethod
    def _migrate_data(cls, data: Dict[str, Any], from_version: int) -> Dict[str, Any]:
        raise ConfigVersionError(
            f"Unable to migrate config from version {from_version} to {cls.VERSION}"
        )
