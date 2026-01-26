from typing import Protocol, TypeVar, Any

from reactivex import Observable


TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class IStream(Protocol[TDesc, TData]):
    @property
    def descriptor(self) -> Observable[TDesc]: ...
    @property
    def observable(self) -> Observable[TData]: ...
