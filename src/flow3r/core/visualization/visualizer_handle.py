from typing import TypeVar, Optional, Any

from PySide6.QtCore import QObject, Signal

from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle, QVisualizerMeta

TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class VisualizerHandle(QObject, IVisualizerHandle[TDesc, TData], metaclass=QVisualizerMeta):
    format_changed = Signal(object)
    item_changed = Signal(object)
    error_changed = Signal(object)
    completed_changed = Signal()

    def __init__(self):
        super().__init__()

        self._desc: Optional[TDesc] = None
        self._item: Optional[TData] = None
        self._error: Optional[Exception] = None
        self._completed = False

    @property
    def format(self) -> Any:
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

    def set_format(self, fmt: TDesc) -> None:
        self._desc = fmt
        self.format_changed.emit(fmt)

    def set_item(self, item: TData) -> None:
        self._item = item
        self.item_changed.emit(item)

    def set_error(self, error: Optional[Exception]) -> None:
        self._error = error
        self.error_changed.emit(error)

    def set_completed(self, completed: bool = True) -> None:
        self._completed = completed
        self.completed_changed.emit()

    def dispose(self):
        pass
