from typing import Protocol, TypeVar, Any

from reactivex import Observable


TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class IStream(Protocol[TDesc, TData]):
    @property
    def format(self) -> TDesc: ...
    @property
    def data(self) -> Observable[TData]: ...
    @property
    def name(self) -> str: ...
    def pipe(self, *ops) -> "IStream[TDesc, Any]": ...
