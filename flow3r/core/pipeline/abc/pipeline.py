from abc import ABC
from typing import Protocol, List, TypeVar, Optional, Tuple, Any, Dict

import reactivex as rx
from reactivex import operators as ops
from reactivex import Observable
from reactivex.abc import DisposableBase
from reactivex.disposable import CompositeDisposable, Disposable

from flow3r.core.api.app.session_context import ISessionContext
from flow3r.core.streaming.abc.stream import IStream

TConfig = TypeVar("TConfig")


class PreviewSubscription:
    def __init__(self, disposable: DisposableBase, preview_done: Observable[Any]):
        self.disposable = disposable
        self.done = preview_done

    def dispose(self):
        self.disposable.dispose()


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


class CompositePreviewSubscription(PreviewSubscription):
    def __init__(self, subscriptions: List[PreviewSubscription]):
        super().__init__(
            CompositeDisposable([sub.disposable for sub in subscriptions]),
            rx.zip(*[sub.done for sub in subscriptions])
        )


class IPipeline(Protocol[TConfig]):
    def configure(self, session_context: ISessionContext, config: TConfig): ...
    def preview(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PreviewSubscription: ...
    def build(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PipelineSubscription: ...
    def dispose(self): ...


class PipelineBase(IPipeline[TConfig], ABC):
    def configure(self, session_context: ISessionContext, config: TConfig):
        pass

    def preview(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PreviewSubscription:
        return PreviewSubscription(Disposable(), rx.from_list([None]))

    def build(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PipelineSubscription:
        return PipelineSubscription(Disposable(), rx.from_list([None]))

    def dispose(self):
        pass
