from abc import ABC, abstractmethod
from typing import Protocol, List, Set, Tuple

from flow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider


class IPipelineConfig(Protocol):
    @property
    def settings_dependencies(self) -> Set[Tuple[str, ...]]: ...
    @property
    def inputs(self) -> List[str]: ...
    @abstractmethod
    def optional_inputs(self) -> List[str]: ...
    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "IPipelineConfig": ...


class PipelineConfigBase(ABC, IPipelineConfig):
    @property
    def settings_dependencies(self) -> Set[Tuple[str, ...]]:
        return set()

    @property
    @abstractmethod
    def inputs(self) -> List[str]: ...

    def optional_inputs(self) -> List[str]:
        return []

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "IPipelineConfig":
        return self
