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
    """Handle returned by :meth:`IPipeline.preview` for a live preview run.

    Call :meth:`dispose` to stop the preview.  Subscribe to :attr:`done` to
    be notified when the preview has finished on its own.
    """

    def __init__(self, disposable: DisposableBase, preview_done: Observable[Any]):
        self.disposable = disposable
        self.done = preview_done
        """Observable that completes when the preview finishes."""

    def dispose(self) -> None:
        """Stop the preview and release resources."""
        self.disposable.dispose()


class PipelineSubscription:
    """Handle returned by :meth:`IPipeline.build` for an active recording/processing run.

    Call :meth:`dispose` to abort the run early.  Subscribe to
    :attr:`primary_done` to be notified when the primary processing step
    finishes (e.g. the video file is flushed and closed) and to
    :attr:`secondary_done` for any follow-up step (e.g. muxing audio+video).

    Attributes:
        primary_done: Observable that emits once the primary processing step completes.
        secondary_done: Observable that emits once any secondary step completes
            (defaults to an immediately-completing observable if unused).
        progress: Observable of ``(completed, total)`` tuples for progress reporting.
    """

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

    def dispose(self) -> None:
        """Abort the pipeline run and release resources."""
        self.disposable.dispose()


class CompositePipelineSubscription(PipelineSubscription):
    """A :class:`PipelineSubscription` that aggregates multiple subscriptions.

    Used internally when a recording group runs more than one pipeline
    simultaneously.  ``primary_done`` / ``secondary_done`` / ``progress``
    complete only when *all* constituent subscriptions have completed.
    """

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
    """A :class:`PreviewSubscription` that aggregates multiple subscriptions.

    ``done`` completes only when *all* constituent previews have finished.
    """

    def __init__(self, subscriptions: List[PreviewSubscription]):
        super().__init__(
            CompositeDisposable([sub.disposable for sub in subscriptions]),
            rx.zip(*[sub.done for sub in subscriptions])
        )


class IPipeline(Protocol[TConfig]):
    """Protocol for a data processing pipeline attached to a recording group.

    A pipeline receives streams from one or more sources and performs an
    operation on them (e.g. encoding video to disk, running pose estimation).

    Lifecycle::

        pipeline.configure(session_context, config)   # called before build/preview
        subscription = pipeline.build(...)            # start recording
        # … recording runs …
        subscription.dispose()                        # stop recording
        pipeline.dispose()                            # release any held resources
    """

    def configure(self, session_context: ISessionContext, config: TConfig) -> None:
        """Configure the pipeline for the upcoming session.

        Called before every :meth:`build` or :meth:`preview` call.  Use this
        to resolve placeholders in file paths and stash any per-session state.

        Args:
            session_context: Provides placeholder resolution and session metadata.
            config: The pipeline's config object as set by the user.
        """
        ...

    def preview(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PreviewSubscription:
        """Start a live preview (non-recording) run.

        Override to display a live feed or analysis result without writing data.
        The default implementation is a no-op.

        Args:
            session_context: Session metadata and placeholder values.
            sources: Mapping of source name → stream for all sources in the group.

        Returns:
            A :class:`PreviewSubscription` that must be disposed to stop the preview.
        """
        ...

    def build(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PipelineSubscription:
        """Start the pipeline (recording or processing run).

        Args:
            session_context: Session metadata and placeholder values.
            sources: Mapping of source name → stream for all sources in the group.

        Returns:
            A :class:`PipelineSubscription` that tracks completion and can be disposed
            to abort the run.
        """
        ...

    def dispose(self) -> None:
        """Release any resources held by the pipeline (models, file handles, threads, …)."""
        ...


class PipelineBase(IPipeline[TConfig], ABC):
    """Convenient base class for pipeline implementations.

    Provides no-op default implementations of all :class:`IPipeline` methods so
    that subclasses only need to override the methods they care about.
    """

    def configure(self, session_context: ISessionContext, config: TConfig) -> None:
        pass

    def preview(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PreviewSubscription:
        return PreviewSubscription(Disposable(), rx.from_list([None]))

    def build(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PipelineSubscription:
        return PipelineSubscription(Disposable(), rx.from_list([None]))

    def dispose(self) -> None:
        pass
