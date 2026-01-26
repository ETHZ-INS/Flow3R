from dataclasses import dataclass
from typing import TypeVar, Generic, Any

from reactivex import Observable

TData = TypeVar("TData")


@dataclass(frozen=True)
class Stream(Generic[TData]):
    descriptor: Observable[Any]
    observable: Observable[TData]
