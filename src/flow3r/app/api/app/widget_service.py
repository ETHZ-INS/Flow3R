import threading
from dataclasses import dataclass
from typing import Dict, Tuple, Callable, Literal, Optional, TypeVar

from PySide6.QtCore import QObject, Signal

from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.core.visualization.visualizer_handle import VisualizerHandle


TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class LeaseVisualizerHandle(IVisualizerHandle[TDesc, TData]):
    def __init__(self, inner: IVisualizerHandle, dispose_cb: Callable[[], None]):
        self._inner = inner
        self._dispose_cb = dispose_cb
        self._disposed = False
        self._lock = threading.Lock()

    def set_format(self, fmt: TDesc) -> None:
        self._inner.set_format(fmt)

    def set_item(self, item: TData) -> None:
        self._inner.set_item(item)

    def set_error(self, error: Optional[Exception]) -> None:
        self._inner.set_error(error)

    def set_completed(self, completed: bool) -> None:
        self._inner.set_completed(completed)

    def dispose(self) -> None:
        with self._lock:
            if self._disposed:
                return
            self._disposed = True
        self._dispose_cb()


@dataclass
class _SourceWidgetEntry:
    widget_id: str
    refcount: int = 0


@dataclass
class _VisualizerWidgetEntry:
    group_id: str
    widget_id: str
    refcount: int = 0


@dataclass
class _SourceHandleEntry:
    widget_id: str
    session_id: str
    handle: IVisualizerHandle
    refcount: int = 0


@dataclass
class _VisualizerHandleEntry:
    group_id: str
    widget_id: str
    session_id: str
    handle: IVisualizerHandle
    refcount: int = 0


class WidgetService(QObject):
    source_handle_added = Signal(str, str, IVisualizerHandle)  # source_id, session_id, handle
    source_handle_removed = Signal(str, str)  # source_id, session_id
    source_assignment_requested = Signal(str, str)  # source_id, session_id
    source_widget_requested = Signal(str)  # source_id
    source_widget_released = Signal(str)  # source_id

    visualizer_handle_added = Signal(str, str, str, IVisualizerHandle)  # group_id, widget_id, session_id, handle
    visualizer_handle_removed = Signal(str, str, str)  # group_id, widget_id, session_id
    visualizer_assignment_requested = Signal(str, str, str)  # group_id, widget_id, session_id
    visualizer_widget_requested = Signal(str, str)  # group_id, widget_id
    visualizer_widget_released = Signal(str, str)  # group_id, widget_id

    recording_controls_requested = Signal(str)
    recording_controls_released = Signal(str)
    recording_controls_location_requested = Signal(str, str, str)

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()

        # handles remain per (widget_id/source_id, session_id)
        self._source_handles: Dict[Tuple[str, str], _SourceHandleEntry] = {}
        self._visualizer_handles: Dict[Tuple[str, str, str], _VisualizerHandleEntry] = {}

        # widget entries per widget_id/source_id
        self._source_widgets: Dict[str, _SourceWidgetEntry] = {}
        self._visualizer_widgets: Dict[Tuple[str, str], _VisualizerWidgetEntry] = {}

    def get_source_handle(self, source_id: str, session_id: str) -> LeaseVisualizerHandle:
        with self._lock:
            if source_id not in self._source_widgets:
                self._source_widgets[source_id] = _SourceWidgetEntry(source_id)
                self.source_widget_requested.emit(source_id)
            self._source_widgets[source_id].refcount += 1

            if (source_id, session_id) not in self._source_handles:
                handle = VisualizerHandle()
                self._source_handles[(source_id, session_id)] = _SourceHandleEntry(source_id, session_id, handle)
                self.source_handle_added.emit(source_id, session_id, handle)
                self.source_assignment_requested.emit(source_id, session_id)
            self._source_handles[(source_id, session_id)].refcount += 1

        handle = self._source_handles[(source_id, session_id)].handle
        return LeaseVisualizerHandle(handle, lambda: self._release_source_lease(source_id, session_id))

    def _release_source_lease(self, source_id: str, session_id: str):
        with self._lock:
            self._source_handles[(source_id, session_id)].refcount -= 1
            if self._source_handles[(source_id, session_id)].refcount == 0:
                del self._source_handles[(source_id, session_id)]
                self.source_handle_removed.emit(source_id, session_id)
            self._source_widgets[source_id].refcount -= 1
            if self._source_widgets[source_id].refcount == 0:
                del self._source_widgets[source_id]
                self.source_widget_released.emit(source_id)

    def get_visualizer_handle(self, group_id: str, widget_id: str, session_id: str) -> LeaseVisualizerHandle:
        with self._lock:
            if (group_id, widget_id) not in self._visualizer_widgets:
                self._visualizer_widgets[(group_id, widget_id)] = _VisualizerWidgetEntry(group_id, widget_id)
                self.visualizer_widget_requested.emit(group_id, widget_id)
            self._visualizer_widgets[group_id, widget_id].refcount += 1

            if (group_id, widget_id, session_id) not in self._visualizer_handles:
                handle = VisualizerHandle()
                self._visualizer_handles[(group_id, widget_id, session_id)] = _VisualizerHandleEntry(group_id, widget_id, session_id, handle)
                self.visualizer_handle_added.emit(group_id, widget_id, session_id, handle)
            self._visualizer_handles[(group_id, widget_id, session_id)].refcount += 1
            self.visualizer_assignment_requested.emit(group_id, widget_id, session_id)

        handle = self._visualizer_handles[(group_id, widget_id, session_id)].handle
        return LeaseVisualizerHandle(handle, lambda: self._release_visualizer_lease(group_id, widget_id, session_id))

    def _release_visualizer_lease(self, group_id: str, widget_id: str, session_id: str):
        with self._lock:
            self._visualizer_handles[(group_id, widget_id, session_id)].refcount -= 1
            if self._visualizer_handles[(group_id, widget_id, session_id)].refcount == 0:
                del self._visualizer_handles[(group_id, widget_id, session_id)]
                self.visualizer_handle_removed.emit(group_id, widget_id, session_id)
            self._visualizer_widgets[group_id, widget_id].refcount -= 1
            if self._visualizer_widgets[group_id, widget_id].refcount == 0:
                del self._visualizer_widgets[group_id, widget_id]
                self.visualizer_widget_released.emit(group_id, widget_id)

    def add_recording_controls(self, group_id: str):
        self.recording_controls_requested.emit(group_id)

    def remove_recording_controls(self, group_id: str):
        self.recording_controls_released.emit(group_id)

    def set_recording_controls_location(self, group_id: str, location: Literal["hidden", "source", "bottom"], source_id: Optional[str] = None):
        self.recording_controls_location_requested.emit(group_id, location, source_id)

class SessionWidgetServiceWrapper:
    def __init__(self, service: WidgetService, group_id: str, session_id: str):
        self._service = service
        self._group_id = group_id
        self._session_id = session_id

    def get_source_handle(self, source_id: str) -> LeaseVisualizerHandle:
        return self._service.get_source_handle(source_id, self._session_id)

    def get_visualizer_handle(self, widget_id: str) -> LeaseVisualizerHandle:
        return self._service.get_visualizer_handle(self._group_id, widget_id, self._session_id)
