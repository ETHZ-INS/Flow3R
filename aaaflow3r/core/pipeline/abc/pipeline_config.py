from abc import ABC
from datetime import datetime
from typing import Self, Protocol

from aaaflow3r.core.placeholder.abc.placeholder_provider import IPlaceholderProvider


class IPipelineConfig(Protocol):
    def resolve(self, placeholder_provider: IPlaceholderProvider) -> Self: ...


class PipelineConfig(ABC):
    def resolve(self, placeholder_provider: IPlaceholderProvider) -> Self:
        return self
