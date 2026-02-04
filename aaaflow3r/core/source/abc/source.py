from typing import TypeVar, Protocol

from aaaflow3r.core.streaming.abc.stream import IStream

TDesc = TypeVar("TDesc")
TData = TypeVar("TData")

class ISource(Protocol[TDesc, TData]):
    @property
    def stream(self) -> IStream[TDesc, TData]: ...
    def open(self): ...
    def close(self): ...
