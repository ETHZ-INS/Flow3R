from abc import ABC, abstractmethod
from typing import Protocol, List, Set, Tuple

from aaaflow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider


class IPipelineConfig(Protocol):
    @property
    def settings_dependencies(self) -> Set[Tuple[str, ...]]: ...
    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "IPipelineConfig": ...
    def inputs(self) -> List[str]: ...


class PipelineConfigBase(ABC, IPipelineConfig):
    @property
    def settings_dependencies(self) -> Set[Tuple[str, ...]]:
        return set()

    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "IPipelineConfig":
        return self

    @abstractmethod
    def inputs(self) -> List[str]: ...
