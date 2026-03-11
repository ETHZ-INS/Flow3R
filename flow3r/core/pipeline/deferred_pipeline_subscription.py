import reactivex as rx
from reactivex import operators as ops
from reactivex.abc import DisposableBase
from reactivex.disposable import CompositeDisposable, Disposable
from reactivex.subject import AsyncSubject

from flow3r.core.pipeline.abc.pipeline import PipelineSubscription


class DeferredPipelineSubscription:
    """
    A helper that lets you return PipelineSubscription immediately,
    then 'fulfill' it later once setup has created real sinks/subscriptions.
    """
    def __init__(self):
        self._disp = CompositeDisposable()
        self._primary_done_subject: AsyncSubject[None] = AsyncSubject()
        self._secondary_done_subject: AsyncSubject[None] = AsyncSubject()

        self._fulfilled = False
        self._disposed = False

        def _dispose():
            self._disposed = True
            self._disp.dispose()
            # Ensure done signals terminate even if disposed before fulfillment
            self._complete_primary()
            self._complete_secondary()

        self.subscription = PipelineSubscription(
            disposable=Disposable(_dispose),
            primary_done=self._primary_done_subject,
            secondary_done=self._secondary_done_subject,
        )

    def _complete_primary(self):
        if not self._primary_done_subject.is_stopped:
            self._primary_done_subject.on_next(None)
            self._primary_done_subject.on_completed()

    def _complete_secondary(self):
        if not self._secondary_done_subject.is_stopped:
            self._secondary_done_subject.on_next(None)
            self._secondary_done_subject.on_completed()

    def fulfill(self, disp: DisposableBase, primary_done: rx.Observable[None], secondary_done: rx.Observable[None] | None = None):
        """
        Attach the real pipeline resources. Can be called once.
        """
        if self._fulfilled:
            raise RuntimeError("DeferredPipelineSubscription.fulfill called twice")
        self._fulfilled = True

        # If already disposed before format arrived, immediately dispose what we just built.
        if self._disposed:
            disp.dispose()
            return

        self._disp.add(disp)

        # Pipe real done -> subjects (complete them exactly once)
        self._disp.add(primary_done.pipe(ops.take(1)).subscribe(
            on_next=lambda _: self._complete_primary(),
            on_error=lambda e: self._complete_primary(),
            on_completed=lambda: None,
        ))

        if secondary_done is not None:
            self._disp.add(secondary_done.pipe(ops.take(1)).subscribe(
                on_next=lambda _: self._complete_secondary(),
                on_error=lambda e: self._complete_secondary(),
                on_completed=lambda: None,
            ))
        else:
            self._complete_secondary()
