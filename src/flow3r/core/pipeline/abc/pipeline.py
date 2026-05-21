from abc import ABC
from typing import Protocol, List, TypeVar, Optional, Tuple, Any, Dict, Generic

import reactivex as rx
from reactivex import operators as ops
from reactivex import Observable
from reactivex.abc import DisposableBase
from reactivex.disposable import CompositeDisposable

from flow3r.core.api.app.settings_view import ISettingsView
from flow3r.core.api.app.widget_service import IWidgetService
from flow3r.core.streaming.abc.stream import IStream

TConfig = TypeVar("TConfig")


class ConfigureContext(Generic[TConfig]):
    """Passed to :meth:`IPipeline.configure`.

    Carries the resolved config, application settings, and the widget service.
    There is no signal registration — ``configure`` is for setting up internal
    state and pre-allocating resources (e.g. loading ML models, creating widget
    handles), not for wiring reactive pipelines.

    Attributes:
        config: The resolved pipeline config for this session.
        settings: Read-only view of application settings.
        widget_service: Service for obtaining visualizer widget handles.
    """

    def __init__(self, config: TConfig, settings: ISettingsView, widget_service: IWidgetService):
        self.config = config
        self.settings = settings
        self.widget_service = widget_service


class PreviewContext(Generic[TConfig]):
    """Passed to :meth:`IPipeline.preview`.

    Carries the resolved config and services, and exposes simple registration
    methods for wiring the preview pipeline.  There is no primary/secondary
    distinction — the preview has a single lifecycle.

    Call :meth:`register_done` exactly once before ``preview()`` returns and
    add any cleanup handles via :meth:`add_disposable`:

    .. code-block:: python

        def preview(self, context: PreviewContext[MyConfig], sources):
            sub = my_sink.subscribe(sources["Video"])
            context.register_done(sub.done)
            context.add_disposable(sub.disposable)

    Attributes:
        config: The resolved pipeline config for this session.
        settings: Read-only view of application settings.
        widget_service: Service for obtaining visualizer widget handles.
    """

    def __init__(self, config: TConfig, settings: ISettingsView, widget_service: IWidgetService):
        self.config = config
        self.settings = settings
        self.widget_service = widget_service

        self._done: Optional[Observable] = None
        self._disposables: List[DisposableBase] = []

    def register_done(self, obs: Observable) -> None:
        """Register the observable that signals preview completion.

        Must be called exactly once before ``preview()`` returns.
        """
        if self._done is not None:
            raise RuntimeError("register_done() called more than once")
        self._done = obs

    def add_disposable(self, disposable: DisposableBase) -> None:
        """Add a disposable that will be released when the preview is stopped."""
        self._disposables.append(disposable)

    def build_subscription(self) -> "PreviewSubscription":
        """Assemble a :class:`PreviewSubscription` from registered signals.

        Raises:
            RuntimeError: If :meth:`register_done` was never called.
        """
        if self._done is None:
            raise RuntimeError(
                "preview() returned without calling context.register_done()"
            )
        return PreviewSubscription(
            disposable=CompositeDisposable(self._disposables),
            preview_done=self._done,
        )


class PipelineContext(Generic[TConfig]):
    """Passed to :meth:`IPipeline.build` for a recording run.

    Carries the resolved config and services, and exposes registration methods
    for wiring the full recording pipeline.  Call :meth:`register_primary_done`
    exactly once before ``build()`` returns.  Optionally call
    :meth:`register_secondary_done` for post-processing (e.g. muxing).

    .. code-block:: python

        def build(self, context: PipelineContext[MyConfig], sources):
            sub = my_sink.subscribe(sources["Video"])
            context.register_primary_done(sub.done)
            context.add_disposable(sub.disposable)

    Attributes:
        config: The resolved pipeline config for this session.
        settings: Read-only view of application settings.
        widget_service: Service for obtaining visualizer widget handles.
        control: Observable that emits ``None`` exactly once when the recording
            gate opens and completes when stop is requested.  Useful for
            pipelines without source inputs and for the
            :class:`~flow3r.core.pipeline.iterative_pipeline.IterativePipeline`
            adapter.
    """

    def __init__(
        self,
        config: TConfig,
        settings: ISettingsView,
        widget_service: IWidgetService,
        control: Observable,
    ):
        self.config = config
        self.settings = settings
        self.widget_service = widget_service
        self.control = control

        self._primary_done: Optional[Observable] = None
        self._secondary_done: Optional[Observable] = None
        self._progress: Optional[Observable[Tuple[int, int]]] = None
        self._disposables: List[DisposableBase] = []

    # ------------------------------------------------------------------
    # Registration API
    # ------------------------------------------------------------------

    def register_primary_done(self, obs: Observable) -> None:
        """Register the observable that signals primary-work completion.

        The observable should emit (or complete) once the core recording work
        is done — e.g. the video file has been flushed and closed.  Must be
        called exactly once before ``build()`` returns.
        """
        if self._primary_done is not None:
            raise RuntimeError("register_primary_done() called more than once")
        self._primary_done = obs

    def register_secondary_done(self, obs: Observable) -> None:
        """Register the observable for secondary (post-processing) completion.

        Optional.  Use for follow-up steps (e.g. muxing) that happen after the
        primary recording files are closed.
        """
        if self._secondary_done is not None:
            raise RuntimeError("register_secondary_done() called more than once")
        self._secondary_done = obs

    def register_progress(self, obs: "Observable[Tuple[int, int]]") -> None:
        """Register an observable that emits ``(completed, total)`` progress tuples."""
        if self._progress is not None:
            raise RuntimeError("register_progress() called more than once")
        self._progress = obs

    def add_disposable(self, disposable: DisposableBase) -> None:
        """Add a disposable that will be disposed when the pipeline is aborted."""
        self._disposables.append(disposable)

    # ------------------------------------------------------------------
    # Internal — called by RuntimeController after build() returns
    # ------------------------------------------------------------------

    def build_subscription(self) -> "PipelineSubscription":
        """Assemble a :class:`PipelineSubscription` from registered signals.

        Raises:
            RuntimeError: If :meth:`register_primary_done` was never called.
        """
        if self._primary_done is None:
            raise RuntimeError(
                "build() returned without calling context.register_primary_done()"
            )
        return PipelineSubscription(
            disposable=CompositeDisposable(self._disposables),
            primary_done=self._primary_done,
            secondary_done=self._secondary_done,
            progress=self._progress,
        )


class PreviewSubscription:
    """Returned internally by :meth:`PreviewContext.build_subscription`.

    The framework uses this to track and dispose an active preview.
    Pipeline authors do not construct this directly — use
    :meth:`PreviewContext.register_done` instead.
    """

    def __init__(self, disposable: DisposableBase, preview_done: Observable[Any]):
        self.disposable = disposable
        self.done = preview_done

    def dispose(self) -> None:
        """Stop the preview and release resources."""
        self.disposable.dispose()


class PipelineSubscription:
    """Returned internally by :meth:`PipelineContext.build_subscription`.

    The framework uses this to track and dispose an active recording run.
    Pipeline authors do not construct this directly — use the registration
    methods on :class:`PipelineContext` instead.

    Attributes:
        primary_done: Observable that emits once the primary processing step completes.
        secondary_done: Observable that emits once any secondary step completes.
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

        pipeline.configure(ConfigureContext(config, settings, widget_service))
        pipeline.build(PipelineContext(config, settings, widget_service, control), sources)
        # … recording runs …
        pipeline.dispose()
    """

    @property
    def supports_preview(self) -> bool:
        """Return ``True`` if this pipeline supports a live preview mode.

        The framework checks this after :meth:`configure` is called, so the
        value may depend on the current config (e.g. a checkbox that enables
        an overlay).  Set the backing field in :meth:`configure`:

        .. code-block:: python

            def configure(self, context):
                self._supports_preview = context.config.show_overlay

            @property
            def supports_preview(self):
                return self._supports_preview

        Defaults to ``False`` — pipelines must explicitly opt in to preview.
        """
        ...

    @property
    def supports_recording(self) -> bool:
        """Return ``True`` if this pipeline supports a recording (build) mode.

        Defaults to ``True``.  Override to ``False`` for viewer-only pipelines
        that only display live data and never write files.
        """
        ...

    def configure(self, context: ConfigureContext[TConfig]) -> None:
        """Configure the pipeline for the upcoming session.

        Called whenever the pipeline config changes and before every
        :meth:`build` or :meth:`preview` call.  Use this to stash per-session
        state and pre-allocate resources such as ML models.  Optional — the
        default implementation is a no-op.

        Args:
            context: Carries the resolved config, settings, and widget service.
        """
        ...

    def preview(self, context: PreviewContext[TConfig], sources: Dict[str, IStream]) -> None:
        """Start a live preview (non-recording) run.

        Override to display a live feed or analysis result without writing
        persistent data.  Register the preview's lifecycle via *context*:

        .. code-block:: python

            def preview(self, context: PreviewContext[MyConfig], sources):
                sub = my_sink.subscribe(sources["Video"])
                context.register_done(sub.done)
                context.add_disposable(sub.disposable)

        The default implementation is a no-op that completes immediately.

        Args:
            context: Carries config, settings, widget service, and registration
                methods.
            sources: Mapping of source name → stream for all sources in the group.
        """
        ...

    def build(self, context: PipelineContext[TConfig], sources: Dict[str, IStream]) -> None:
        """Start the pipeline (recording or processing run).

        Register completion signals via *context* rather than returning a value:

        .. code-block:: python

            def build(self, context: PipelineContext[MyConfig], sources):
                sub = my_sink.subscribe(sources["Video"])
                context.register_primary_done(sub.done)
                context.add_disposable(sub.disposable)

        Args:
            context: Carries config, settings, widget service, ``control``
                observable, and registration methods for done/progress signals.
            sources: Mapping of source name → stream for all sources in the group.
        """
        ...

    def dispose(self) -> None:
        """Release any resources held by the pipeline (models, file handles, threads, …)."""
        ...


class PipelineBase(IPipeline[TConfig], ABC):
    """Convenient base class for pipeline implementations.

    Provides no-op default implementations of all :class:`IPipeline` methods so
    that subclasses only need to override the methods they care about.

    Default capability flags: ``supports_preview = False``,
    ``supports_recording = True``.  Override either property (or set the
    backing field in :meth:`configure`) to change per-instance.
    """

    @property
    def supports_preview(self) -> bool:
        return False

    @property
    def supports_recording(self) -> bool:
        return True

    def configure(self, context: ConfigureContext[TConfig]) -> None:
        pass

    def preview(self, context: PreviewContext[TConfig], sources: Dict[str, IStream]) -> None:
        context.register_done(rx.from_list([None]))

    def build(self, context: PipelineContext[TConfig], sources: Dict[str, IStream]) -> None:
        context.register_primary_done(rx.from_list([None]))

    def dispose(self) -> None:
        pass
