from abc import ABC, abstractmethod
from typing import Self, Protocol, List

from aaaflow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider


class IPipelineConfig(Protocol):
    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "IPipelineConfig": ...
    def inputs(self) -> List[str]: ...


class PipelineConfigBase(ABC, IPipelineConfig):
    def resolve(self, placeholder_provider: IPlaceholderProvider) -> "IPipelineConfig":
        return self

    @abstractmethod
    def inputs(self) -> List[str]: ...
