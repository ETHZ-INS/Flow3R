"""IterativePipeline — an adapter base class for single-threaded, imperative pipelines.

Data scientists who are unfamiliar with reactive programming can subclass
:class:`IterativePipeline` and override :meth:`run` with a regular Python
method that iterates over each source as a plain Python iterator:

.. code-block:: python

    class MyPipeline(IterativePipeline[MyConfig]):
        def configure(self, session_context, config: MyConfig):
            self._output_path = Path(config.output_file)

        def run(self, sources: Dict[str, Iterable]) -> None:
            with open(self._output_path, "w") as f:
                for frame in sources["Video"]:
                    result = my_model.predict(frame)
                    f.write(result.to_json() + "\\n")

The framework calls :meth:`run` on a background thread when the recording
gate opens and signals ``primary_done`` when the thread finishes (normally
or with an exception).  The source iterators stop yielding items and raise
:class:`StopIteration` as soon as the recording stop is requested.
"""

import queue
import threading
from typing import Dict, Generic, Iterable, Iterator, Optional, TypeVar

from reactivex.subject import AsyncSubject

from flow3r.core.pipeline.abc.pipeline import PipelineBase, PipelineContext
from flow3r.core.streaming.abc.stream import IStream

TConfig = TypeVar("TConfig")


class _ObservableIterator(Iterator):
    """Bridges an RxPY observable into a blocking Python iterator.

    Items emitted by the observable are placed onto an internal queue so
    the consuming thread can pull them synchronously.  The iterator raises
    :class:`StopIteration` when the observable completes and propagates any
    observable error as an exception.
    """

    _SENTINEL = object()

    def __init__(self, observable):
        self._q: queue.Queue = queue.Queue()
        self._error: Optional[BaseException] = None
        self._sub = observable.subscribe(
            on_next=lambda item: self._q.put(item),
            on_error=lambda exc: (self._q.put(self._SENTINEL), setattr(self, "_error", exc)),
            on_completed=lambda: self._q.put(self._SENTINEL),
        )

    def __iter__(self) -> Iterator:
        return self

    def __next__(self):
        item = self._q.get()
        if item is self._SENTINEL:
            if self._error is not None:
                raise self._error
            raise StopIteration
        return item

    def dispose(self) -> None:
        self._sub.dispose()
        # Unblock any waiting thread so it can exit cleanly.
        self._q.put(self._SENTINEL)


class IterativePipeline(PipelineBase[TConfig], Generic[TConfig]):
    """Base class for imperative, single-threaded pipeline implementations.

    Override :meth:`run` to process frames one by one.  The method receives
    each source as a regular Python :class:`~collections.abc.Iterable`; just
    iterate over it until it is exhausted (which happens automatically when
    the recording stop is requested).

    The default ``configure``, ``preview``, and ``dispose`` implementations
    from :class:`~flow3r.core.pipeline.abc.pipeline.PipelineBase` are
    inherited unchanged.
    """

    def run(self, sources: Dict[str, Iterable]) -> None:
        """Process frames until all source iterables are exhausted.

        Args:
            sources: Mapping of input name → iterable of data items.
                Each iterable yields items until the recording stop is
                requested, then raises :class:`StopIteration`.

        Raises:
            Any exception raised here is forwarded to ``primary_done``
            as an observable error.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.run() is not implemented"
        )

    # ------------------------------------------------------------------
    # PipelineBase override — internal plumbing
    # ------------------------------------------------------------------

    def build(self, context: PipelineContext, sources: Dict[str, IStream]) -> None:
        done_subject: AsyncSubject = AsyncSubject()
        context.register_primary_done(done_subject)

        iterators = {name: _ObservableIterator(stream.data) for name, stream in sources.items()}

        def _dispose_iterators():
            for it in iterators.values():
                it.dispose()

        def _thread_target():
            try:
                self.run({name: it for name, it in iterators.items()})
                done_subject.on_next(None)
                done_subject.on_completed()
            except Exception as exc:
                done_subject.on_error(exc)
            finally:
                _dispose_iterators()

        def _on_start(_):
            thread = threading.Thread(target=_thread_target, daemon=True)
            thread.start()

        def _on_stop():
            # Completion of control signals stop — unblock the iterators so
            # the run() method exits naturally via StopIteration.
            _dispose_iterators()

        context.add_disposable(
            context.control.subscribe(on_next=_on_start, on_completed=_on_stop)
        )

