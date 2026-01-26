import threading
from dataclasses import dataclass
from typing import Dict, Tuple, Callable

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QMainWindow, QDockWidget

from aaaflow3r.app.visualization.source_widget import SourceWidget
from aaaflow3r.app.visualization.visualizer_widget import VisualizerWidget
from aaaflow3r.app.widgets.recording_controls_widget import RecordingControlsWidget
from aaaflow3r.core.streaming.abc.stream import IStream
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.core.visualization.abc.visualizer_type import IVisualizerType
from aaaflow3r.core.visualization.visualizer_handle import VisualizerHandle


class LeaseVisualizerHandle(IVisualizerHandle):
    def __init__(self, inner: IVisualizerHandle, dispose_cb: Callable[[], None]):
        self._inner = inner
        self._dispose_cb = dispose_cb
        self._disposed = False
        self._lock = threading.Lock()

    def subscribe(self, stream: IStream):
        self._inner.subscribe(stream)

    def unsubscribe(self):
        self._inner.unsubscribe()

    def dispose(self) -> None:
        with self._lock:
            if self._disposed:
                return
            self._disposed = True
        self._dispose_cb()


@dataclass
class _WidgetEntry:
    widget_id: str
    widget: QDockWidget
    refcount: int = 0


@dataclass
class _HandleEntry:
    widget_id: str
    session_id: str
    handle: IVisualizerHandle
    refcount: int = 0


class WidgetService(QObject):
    request_widget = Signal(str, str, str, bool)  # widget_type_name, widget_id, session_id, is_source
    release_widget = Signal(str)                  # widget_id (UI-thread teardown)

    def __init__(self, dock_window: QMainWindow, widget_types: Dict[str, IVisualizerType]):
        super().__init__()
        self._dock_window = dock_window
        self._widget_types = widget_types

        self._lock = threading.Lock()

        self.controller = None

        # handles remain per (widget_id, session_id)
        self._handles: Dict[Tuple[str, str], _HandleEntry] = {}

        # widget entries per widget_id
        self._entries: Dict[str, _WidgetEntry] = {}

        self.request_widget.connect(self._ensure_widget_and_connect)
        self.release_widget.connect(self._teardown_widget)

    def get_visualizer_handle(
        self,
        widget_type_name: str,
        widget_id: str,
        session_id: str,
        is_source: bool = False,
    ) -> LeaseVisualizerHandle:
        """
        Call from worker or UI thread.
        Returns a lease with `lease.handle` and `lease.dispose()`.
        """
        with self._lock:
            if (widget_id, session_id) in self._handles:
                handle = self._handles[(widget_id, session_id)].handle
            else:
                handle = VisualizerHandle()

                handle_entry = _HandleEntry(widget_id, session_id, handle)
                self._handles[(widget_id, session_id)] = handle_entry

            self._increment_refcount(widget_id, session_id)

        self.request_widget.emit(widget_type_name, widget_id, session_id, is_source)

        return LeaseVisualizerHandle(
            inner=handle,
            dispose_cb=lambda: self._release_lease(widget_id, session_id)
        )

    def _increment_refcount(self, widget_id: str, session_id: str) -> None:
        handle_entry = self._handles.get((widget_id, session_id))
        if handle_entry is not None:
            handle_entry.refcount += 1

        entry = self._entries.get(widget_id)
        if entry is None:
            # placeholder until UI actually creates widget/dock
            self._entries[widget_id] = _WidgetEntry(
                widget_id=widget_id,
                widget=None,   # type: ignore
                refcount=1,
            )
        else:
            entry.refcount += 1

    def _release_lease(self, widget_id: str, session_id: str) -> None:
        """
        Decrease refcount; if hits 0, schedule widget teardown in UI thread.
        Also dispose/remove the per-session handle if you want.
        """
        needs_release = False
        with self._lock:
            handle_entry = self._handles.get((widget_id, session_id))
            if handle_entry is not None:
                handle_entry.refcount -= 1
                if handle_entry.refcount <= 0:
                    try:
                        handle_entry.handle.dispose()
                    except Exception:
                        pass
                    del self._handles[(widget_id, session_id)]

            widget_entry = self._entries.get(widget_id)
            if widget_entry is not None:
                widget_entry.refcount -= 1
                if widget_entry.refcount <= 0:
                    # schedule UI teardown
                    needs_release = True

        if needs_release:
            self.release_widget.emit(widget_id)

    @Slot(str, str, str, bool)
    def _ensure_widget_and_connect(self, widget_type_name: str, widget_id: str, session_id: str, is_source: bool):
        """
        UI thread: create widget/dock if missing; connect widget to the handle.
        """
        with self._lock:
            handle_entry = self._handles.get((widget_id, session_id))
            widget_entry = self._entries.get(widget_id)

        if handle_entry is None or widget_entry is None:
            return  # lease ended or widget got torn down

        if widget_entry.widget is None:
            widget_type = self._widget_types[widget_type_name]
            visualizer = widget_type.widget_factory(self._dock_window)

            if is_source:
                widget = SourceWidget(widget_id, self._dock_window)
                widget.setup_source.connect(self.controller.setup_source)

                recording_controls = RecordingControlsWidget(widget_id, "My Recording")
                recording_controls.session_id = "My Session"
                recording_controls.recording_start.connect(self.controller.start_recording)
                widget.set_recording_controls_widget(recording_controls)
            else:
                widget = VisualizerWidget(self._dock_window)

            widget.setObjectName(widget_id)
            widget.set_visualizer(visualizer)

            # Try to restore dock widget in its last known position
            if not self._dock_window.restoreDockWidget(widget):
                self._dock_window.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, widget)

            with self._lock:
                self._entries[widget_id].widget = widget

        with self._lock:
            # re-fetch widget (or keep widget ref)
            widget = self._entries.get(widget_id).widget if self._entries.get(widget_id) else None

        if widget is None:
            return

        widget.set_handle(handle_entry.handle)

    @Slot(str)
    def _teardown_widget(self, widget_id: str) -> None:
        """
        UI thread: remove widget. Safe to call multiple times.
        """
        with self._lock:
            entry = self._entries.get(widget_id)
            if entry is None or entry.refcount > 0:
                return
            widget = entry.widget
            self._entries.pop(widget_id, None)

        # Remove from UI
        if widget is not None:
            try:
                self._dock_window.removeDockWidget(widget)
            except Exception:
                pass
            widget.set_visualizer(None)
            widget.deleteLater()
