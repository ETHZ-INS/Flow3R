from dataclasses import dataclass
from typing import TypeVar, Generic, Any

from reactivex import Observable

TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


@dataclass(frozen=True)
class Stream(Generic[TDesc, TData]):
    descriptor: Observable[TDesc]
    observable: Observable[TData]

    def pipe(self, *ops) -> "Stream[TDesc, Any]":
        return Stream(self.descriptor, self.observable.pipe(*ops))
