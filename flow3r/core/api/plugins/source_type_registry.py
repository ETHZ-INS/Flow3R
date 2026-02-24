from typing import Protocol

from flow3r.core.source.abc.source_type import ISourceType


class ISourceTypeRegistry(Protocol):
    def register(self, source_type: ISourceType): ...
