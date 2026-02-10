from concurrent.futures import Future
from dataclasses import dataclass
from typing import Protocol, List, TypeVar, Optional, Tuple

from reactivex import Observable
from reactivex.abc import DisposableBase

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.streaming.abc.stream import IStream

TConfig = TypeVar("TConfig")


class PipelineSubscription:
    def __init__(
        self,
        disposable: DisposableBase,
        primary_done: Future[None],
        secondary_done: Optional[Future[None]] = None,
        progress: Optional[Observable[Tuple[int, int]]] = None
    ):
        self.disposable = disposable
        self.primary_done = primary_done
        self.secondary_done = secondary_done if secondary_done else primary_done
        self.progress = progress

    def dispose(self):
        self.disposable.dispose()


class IPipeline(Protocol[TConfig]):
    def configure(self, app_context: IAppContext, config: TConfig): ...
    def build(self, app_context: IAppContext, sources: List[IStream]) -> PipelineSubscription: ...
    def dispose(self): ...
