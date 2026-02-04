from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

from reactivex.abc import DisposableBase
from reactivex.disposable import Disposable
from reactivex import operators as ops, Observable
from reactivex.subject import ReplaySubject

from aaaflow3r.core.streaming.abc.stream import IStream

TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


@dataclass(frozen=True)
class SinkSubscription:
    """Returned by Sink.subscribe()."""
    disposable: Disposable
    done: Observable[None]  # emits nothing; completes when cleanup finished

    def dispose(self):
        self.disposable.dispose()


class Sink(Generic[TDesc, TData], ABC):
    """
    Base class for sink nodes consuming a stream with a single, immutable descriptor.

    Override:
      - setup(desc): allocate/open resources (called once, from descriptor)
      - on_next(item): consume each item
      - cleanup(): release resources (called exactly once)

    Guarantees:
      - setup() is called once (descriptor.take(1))
      - on_next() is only called after successful setup()
      - cleanup() is called exactly once on completed/error/dispose
      - if on_next raises, cleanup runs and the subscription is disposed
    """

    @abstractmethod
    def setup(self, desc: TDesc) -> None: ...

    @abstractmethod
    def on_next(self, item: TData) -> None: ...

    def on_error(self, exc: Exception) -> None:
        """Optional hook (default no-op). cleanup still runs."""
        return None

    def on_completed(self) -> None:
        """Optional hook (default no-op). cleanup still runs."""
        return None

    @abstractmethod
    def cleanup(self) -> None: ...

    def subscribe(self, stream: IStream[TData, TDesc]) -> SinkSubscription:
        closed = False
        data_sub: Optional[DisposableBase] = None
        desc_sub: Optional[DisposableBase] = None

        done_subject: ReplaySubject[None] = ReplaySubject(1)

        def cleanup_once():
            nonlocal closed, data_sub, desc_sub
            if closed:
                return
            closed = True

            # Stop data first to prevent further on_next calls.
            if data_sub is not None:
                data_sub.dispose()
                data_sub = None

            # Descriptor subscription is take(1) so it's usually already done,
            # but dispose it anyway for safety.
            if desc_sub is not None:
                desc_sub.dispose()
                desc_sub = None

            try:
                self.cleanup()
            except Exception:
                # Never let cleanup exceptions escape; at most log externally.
                pass
            finally:
                done_subject.on_next(None)
                done_subject.on_completed()

        def start_data_subscription():
            nonlocal data_sub

            def _on_next(item: TData):
                # If disposed, ignore late emissions.
                if closed:
                    return

                try:
                    self.on_next(item)
                except Exception as exc:
                    # Ensure resources are released even if user code throws.
                    try:
                        self.on_error(exc)
                    finally:
                        cleanup_once()
                    # Re-raise so the error is visible to upstream error handlers/logging.
                    raise

            def _on_error(exc: Exception):
                if closed:
                    return
                try:
                    self.on_error(exc)
                finally:
                    cleanup_once()

            def _on_completed():
                if closed:
                    return
                try:
                    self.on_completed()
                finally:
                    cleanup_once()

            data_sub = stream.observable.subscribe(_on_next, _on_error, _on_completed)

        def _on_desc(desc: TDesc):
            if closed:
                return
            try:
                self.setup(desc)
            except Exception as exc:
                # setup failed; call on_error hook then cleanup and surface error
                try:
                    self.on_error(exc)
                finally:
                    cleanup_once()
                raise

            start_data_subscription()

        def _on_desc_error(exc: Exception):
            if closed:
                return
            try:
                self.on_error(exc)
            finally:
                cleanup_once()

        # Immutable format: take only the first descriptor.
        desc_sub = stream.descriptor.pipe(ops.take(1)).subscribe(_on_desc, _on_desc_error)

        # Disposing the returned Disposable always triggers cleanup.
        disposable = Disposable(cleanup_once)
        return SinkSubscription(disposable, done_subject.pipe(ops.take(1)))
