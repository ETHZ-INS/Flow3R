from concurrent.futures import Future
from dataclasses import dataclass
from typing import Protocol, List, TypeVar, Optional, Tuple, Any

import reactivex as rx
from reactivex import operators as ops
from reactivex import Observable
from reactivex.abc import DisposableBase
from reactivex.disposable import CompositeDisposable

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.streaming.abc.stream import IStream

TConfig = TypeVar("TConfig")


class PipelineSubscription:
    def __init__(
        self,
        disposable: DisposableBase,
        primary_done: Observable[Any],
        secondary_done: Optional[Observable[Any]] = None,
        progress: Optional[Observable[Tuple[int, int]]] = None
    ):
        self.disposable = disposable
        self.primary_done = primary_done
        self.secondary_done = secondary_done or rx.from_list([None])
        self.progress = progress or rx.from_list([(0, 0)])

    def dispose(self):
        self.disposable.dispose()


class CompositePipelineSubscription(PipelineSubscription):
    def __init__(self, subscriptions: List[PipelineSubscription]):
        super().__init__(
            CompositeDisposable([sub.disposable for sub in subscriptions]),
            rx.zip(*[sub.primary_done for sub in subscriptions]),
            rx.zip(*[sub.secondary_done for sub in subscriptions]),
            rx.zip(*[sub.progress for sub in subscriptions]).pipe(
                ops.map(lambda progresses: (sum(p[0] for p in progresses), sum(p[1] for p in progresses)))
            )
        )


class IPipeline(Protocol[TConfig]):
    def configure(self, app_context: IAppContext, config: TConfig): ...
    def build(self, app_context: IAppContext, sources: List[IStream]) -> PipelineSubscription: ...
    def dispose(self): ...
