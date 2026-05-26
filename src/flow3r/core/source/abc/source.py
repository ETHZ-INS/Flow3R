from typing import TypeVar, Protocol

from flow3r.core.streaming.abc.stream import IStream

TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class ISource(Protocol[TDesc, TData]):
    """Protocol for a single data source (camera, microphone, file, …).

    A source encapsulates one *device or file* and exposes its data as a
    reactive stream.  The application calls :meth:`open` before subscribing
    to the stream and :meth:`close` when the source is no longer needed.

    Type parameters:
        TDesc: Descriptor type emitted by the stream (e.g. frame metadata).
        TData: Data type emitted by the stream (e.g. ``numpy.ndarray`` for video).
    """

    @property
    def stream(self) -> IStream[TDesc, TData]:
        """The reactive stream that emits items from this source."""
        ...

    def open(self) -> None:
        """Open/initialize the underlying device or file and start producing items."""
        ...

    def close(self) -> None:
        """Stop producing items and release all resources held by this source."""
        ...
