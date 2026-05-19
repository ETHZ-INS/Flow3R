from abc import ABC, abstractmethod, abstractproperty
from typing import Protocol, List, Set, Tuple, Self, Mapping, Any, ClassVar

from flow3r.core.config.abc.config import ConfigBase, ITypedConfig
from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider


class IPipelineConfig(ITypedConfig, Protocol):
    @property
    def settings_dependencies(self) -> Set[Tuple[str, ...]]: ...
    @property
    def inputs(self) -> List[str]: ...
    @property
    def optional_inputs(self) -> List[str]: ...
    @property
    def files(self) -> List[str]: ...
    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "IPipelineConfig": ...


class PipelineConfigBase(ConfigBase, IPipelineConfig, ABC):
    TYPE_ID: ClassVar[str]

    @property
    def settings_dependencies(self) -> Set[Tuple[str, ...]]:
        return set()

    @property
    @abstractmethod
    def inputs(self) -> List[str]: ...

    @property
    def optional_inputs(self) -> List[str]:
        return []

    @property
    def files(self) -> List[str]:
        return []

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> Self:
        return self
