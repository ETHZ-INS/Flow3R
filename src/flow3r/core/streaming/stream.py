from dataclasses import dataclass
from typing import TypeVar, Generic, Any

from reactivex import Observable

TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


@dataclass(frozen=True)
class Stream(Generic[TDesc, TData]):
    format: TDesc
    data: Observable[TData]
    name: str = ""

    def pipe(self, *ops) -> "Stream[TDesc, Any]":
        return Stream(self.format, self.data.pipe(*ops))
