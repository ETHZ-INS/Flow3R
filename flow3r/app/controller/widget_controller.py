from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Literal, Tuple, List

from PySide6.QtCore import QObject, Slot, Qt, Signal
from PySide6.QtWidgets import QMainWindow, QWidget

from flow3r.app.visualization.source_widget import SourceWidget
from flow3r.app.visualization.visualizer_widget import VisualizerWidget
from flow3r.app.widgets.recording_controls_widget import RecordingControlsWidget
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.core.visualization.abc.visualizer_type import IVisualizerType


@dataclass
class _RecordingControlsWidgetEntry:
    widget: RecordingControlsWidget
    location: Literal["hidden", "source", "bottom"] = "hidden"
    source_id: Optional[str] = None


class WidgetController(QObject):
    """
    UI thread only.
    Owns widget instances and their UI wiring.
    """

    source_snapshot_requested = Signal(str)
    group_snapshot_requested = Signal(str)

    def __init__(self, dock_window: QMainWindow, bottom_widget: QWidget, visualizer_types: List[IVisualizerType]):
        super().__init__()
        self._dock_window = dock_window
        self._bottom_widget = bottom_widget
        self._visualizer_types = visualizer_types

        self._main_window = None
        self._controller = None

        self._source_handles: Dict[str, Dict[str, IVisualizerHandle]] = {}
        self._visualizer_handles: Dict[Tuple[str, str], Dict[str, IVisualizerHandle]] = {}

        self._source_widgets: Dict[str, SourceWidget] = {}
        self._visualizer_widgets: Dict[Tuple[str, str], VisualizerWidget] = {}
        self._recording_control_widgets: Dict[str, _RecordingControlsWidgetEntry] = {}

    def set_controller(self, controller):
        assert self._controller is None
        self._controller = controller
        self.source_snapshot_requested.connect(controller.send_source_snapshot)
        self.group_snapshot_requested.connect(controller.send_group_snapshot)

    @Slot(str, str, object)
    def add_source_handle(self, source_id: str, session_id: str, handle: IVisualizerHandle) -> None:
        if source_id not in self._source_handles:
            self._source_handles[source_id] = {}
        self._source_handles[source_id][session_id] = handle

    @Slot(str, str)
    def remove_source_handle(self, source_id: str, session_id: str) -> None:
        self._source_handles[source_id].pop(session_id, None)

    @Slot(str, str, object)
    def add_visualizer_handle(self, group_id: str, widget_id: str, session_id: str, handle: IVisualizerHandle) -> None:
        if widget_id not in self._visualizer_handles:
            self._visualizer_handles[(group_id, widget_id)] = {}
        self._visualizer_handles[(group_id, widget_id)][session_id] = handle

    @Slot(str, str)
    def remove_visualizer_handle(self, group_id: str, widget_id: str, session_id: str) -> None:
        self._visualizer_handles[(group_id, widget_id)].pop(session_id, None)

    @Slot(str)
    def create_source_widget(self, source_id: str) -> None:
        assert source_id not in self._source_widgets
        widget = SourceWidget(self._visualizer_types, source_id, self._dock_window)
        widget.setObjectName("source_widget_" + source_id)
        widget.setup_source.connect(self._controller.setup_source)
        widget.edit_source.connect(self._main_window._edit_source)
        widget.group_snapshot_requested.connect(self._controller.send_group_snapshot)

        self._controller.source_snapshot.connect(widget.source_changed)
        self._controller.source_changed.connect(widget.source_changed)
        self._controller.group_snapshot.connect(widget.group_changed)
        self._controller.group_changed.connect(widget.group_changed)

        self.source_snapshot_requested.emit(source_id)

        self._source_widgets[source_id] = widget
        if not self._dock_window.restoreDockWidget(widget):
            self._dock_window.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, widget)

    @Slot(str)
    def destroy_source_widget(self, source_id: str) -> None:
        widget = self._source_widgets.pop(source_id, None)
        if widget:
            widget.set_handle(None)
            if widget.recording_controls_widget:
                widget.recording_controls_widget.setParent(self._bottom_widget)
            self._dock_window.removeDockWidget(widget)
            widget.deleteLater()

    @Slot(str, object)
    def assign_source_handle(self, source_id: str, session_id: str) -> None:
        handle = self._source_handles[source_id][session_id]
        widget = self._source_widgets[source_id]
        widget.set_handle(handle)

    @Slot(str, str, bool)
    def create_visualizer_widget(self, group_id: str, widget_id: str) -> None:
        assert (group_id, widget_id) not in self._visualizer_widgets
        widget = VisualizerWidget(self._visualizer_types, self._dock_window)
        widget.setObjectName("visualizer_widget_" + group_id + "_" + widget_id)
        widget.setWindowTitle(widget_id)
        self._visualizer_widgets[(group_id, widget_id)] = widget
        if not self._dock_window.restoreDockWidget(widget):
            self._dock_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, widget)

    @Slot(str)
    def destroy_visualizer_widget(self, group_id: str, widget_id: str) -> None:
        widget = self._visualizer_widgets.pop((group_id, widget_id), None)
        if widget:
            widget.set_handle(None)
            self._dock_window.removeDockWidget(widget)
            widget.deleteLater()

    @Slot(str, object)
    def assign_visualizer_handle(self, group_id: str, widget_id: str, session_id: str) -> None:
        handle = self._visualizer_handles[(group_id, widget_id)][session_id]
        widget = self._visualizer_widgets[(group_id, widget_id)]
        widget.set_handle(handle)

    @Slot(str)
    def create_recording_controls_widget(self, group_id: str) -> None:
        assert group_id not in self._recording_control_widgets
        widget = RecordingControlsWidget(group_id, "Unknown", parent=self._bottom_widget)
        widget.recording_start.connect(self._controller.start_recording)
        widget.recording_stop.connect(self._controller.stop_recording)
        widget.active_session_requested.connect(self._controller.send_active_session_snapshot)
        self._controller.group_snapshot.connect(widget.group_changed)
        self._controller.group_changed.connect(widget.group_changed)
        self._controller.active_session_snapshot.connect(widget.set_active_session)
        self._controller.active_session_changed.connect(widget.set_active_session)
        self._controller.session_state_changed.connect(widget.set_session_state)
        widget.request_active_session()

        self.group_snapshot_requested.emit(group_id)

        entry = _RecordingControlsWidgetEntry(widget)
        self._recording_control_widgets[group_id] = entry
        self._bottom_widget.layout().addWidget(widget)
        widget.setVisible(False)

    @Slot(str)
    def remove_recording_controls_widget(self, group_id: str) -> None:
        entry = self._recording_control_widgets.pop(group_id, None)
        if entry:
            if entry.location == "source":
                old_source_widget = self._source_widgets[entry.source_id]
                old_source_widget.set_recording_controls_widget(None)
            elif entry.location == "bottom":
                self._bottom_widget.layout().removeWidget(entry.widget)
            elif entry.location == "hidden":
                self._bottom_widget.layout().removeWidget(entry.widget)
            entry.widget.deleteLater()

    @Slot(str, str, object)
    def set_recording_controls_widget_location(self, group_id: str, location: Literal["hidden", "source", "bottom"], source_id: Optional[str] = None) -> None:
        entry = self._recording_control_widgets[group_id]
        if location == "source":
            assert source_id is not None

        if entry.location == location and entry.source_id == source_id:
            return

        if entry.location == "source":
            old_source_widget = self._source_widgets[entry.source_id]
            old_source_widget.set_recording_controls_widget(None)
        elif entry.location == "bottom":
            self._bottom_widget.layout().removeWidget(entry.widget)
        elif entry.location == "hidden":
            self._bottom_widget.layout().removeWidget(entry.widget)

        if location == "source":
            source_widget = self._source_widgets[source_id]
            source_widget.set_recording_controls_widget(entry.widget)
            entry.widget.setVisible(True)
            entry.widget.hide_group_name()
            entry.location = location
            entry.source_id = source_id
        elif location == "bottom":
            self._bottom_widget.layout().addWidget(entry.widget)
            entry.widget.setVisible(True)
            entry.widget.show_group_name()
            entry.location = location
            entry.source_id = None
        elif location == "hidden":
            self._bottom_widget.layout().addWidget(entry.widget)
            entry.widget.setVisible(False)
            entry.location = location
            entry.source_id = None
