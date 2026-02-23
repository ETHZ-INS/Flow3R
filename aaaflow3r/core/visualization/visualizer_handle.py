from typing import TypeVar, Optional

from PySide6.QtCore import QObject, Signal
from reactivex.abc import DisposableBase

from aaaflow3r.core.streaming.abc.stream import IStream
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle, QVisualizerMeta

TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class VisualizerHandle(QObject, IVisualizerHandle[TDesc, TData], metaclass=QVisualizerMeta):
    desc_changed = Signal(str)
    item_changed = Signal(object)
    error_changed = Signal(object)
    completed_changed = Signal()

    def __init__(self):
        super().__init__()

        self._desc_sub: Optional[DisposableBase] = None
        self._sub: Optional[DisposableBase] = None
        self._desc: Optional[TDesc] = None
        self._item: Optional[TData] = None
        self._error: Optional[Exception] = None
        self._completed = False

    @property
    def desc(self) -> str:
        return self._desc

    @property
    def item(self) -> Optional[TData]:
        return self._item

    @property
    def error(self) -> Optional[Exception]:
        return self._error

    @property
    def completed(self) -> bool:
        return self._completed

    def subscribe(self, stream: IStream[TDesc, TData]):
        self.unsubscribe()
        self._desc_sub = stream.descriptor.subscribe(self._on_desc, self._on_error)
        self._sub = stream.observable.subscribe(self._on_next, self._on_error, self._on_completed)

    def unsubscribe(self):
        if self._sub:
            self._sub.dispose()
            self._sub = None
        if self._desc_sub:
            self._desc_sub.dispose()
            self._desc_sub = None

    def dispose(self):
        self.unsubscribe()

    def _on_desc(self, desc: TDesc):
        self._desc = desc
        self.desc_changed.emit(desc)

    def _on_next(self, item: TData):
        self._item = item
        self.item_changed.emit(item)

    def _on_error(self, error: Exception):
        self._error = error
        self.error_changed.emit(error)

    def _on_completed(self):
        self._completed = True
        self.completed_changed.emit()
