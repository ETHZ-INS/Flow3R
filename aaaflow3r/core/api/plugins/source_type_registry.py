from typing import Protocol

from aaaflow3r.core.source.abc.source_type import ISourceType


class ISourceTypeRegistry(Protocol):
    def register(self, source_type: ISourceType): ...
