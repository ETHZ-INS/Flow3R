from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

from reactivex.abc import DisposableBase
from reactivex.disposable import Disposable
from reactivex import Observable
from reactivex.subject import ReplaySubject

from flow3r.core.streaming.abc.stream import IStream
from flow3r.logger import get_logger

_logger = get_logger(__name__)

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
    Base class for sink nodes consuming a stream with a single, immutable format.

    Override:
      - setup(desc): allocate/open resources (called once, eagerly)
      - on_next(item): consume each item
      - cleanup(): release resources (called exactly once)

    Guarantees:
      - setup() is called once before subscribing to the data stream
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

    def subscribe(self, stream: IStream[TDesc, TData]) -> SinkSubscription:
        closed = False
        data_sub: Optional[DisposableBase] = None

        done_subject: ReplaySubject[None] = ReplaySubject(1)

        def cleanup_once(exc: Optional[Exception] = None):
            nonlocal closed, data_sub
            if closed:
                return
            closed = True

            try:
                if data_sub is not None:
                    data_sub.dispose()
                    data_sub = None
                self.cleanup()
            except Exception:
                pass
            finally:
                _logger.debug("Sink done %s exc=%s", self.__class__.__name__, exc)
                if exc is not None:
                    done_subject.on_error(exc)
                else:
                    done_subject.on_next(None)
                    done_subject.on_completed()

        # Eager one-time setup from the simple format.
        try:
            self.setup(stream.format)
        except Exception as exc:
            try:
                self.on_error(exc)
            finally:
                cleanup_once(exc)
            return SinkSubscription(Disposable(), done_subject)

        def _on_next(item: TData):
            if closed:
                return

            try:
                self.on_next(item)
            except Exception as exc:
                try:
                    self.on_error(exc)
                finally:
                    cleanup_once(exc)
                raise

        def _on_error(exc: Exception):
            if closed:
                return
            try:
                self.on_error(exc)
            finally:
                cleanup_once(exc)

        def _on_completed():
            if closed:
                return
            try:
                self.on_completed()
            finally:
                cleanup_once()

        try:
            data_sub = stream.data.subscribe(_on_next, _on_error, _on_completed)
        except Exception as exc:
            try:
                self.on_error(exc)
            finally:
                cleanup_once(exc)

        disposable = Disposable(cleanup_once)
        return SinkSubscription(disposable, done_subject)
