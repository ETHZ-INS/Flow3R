from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Literal, Tuple, List

from PySide6.QtCore import QObject, Slot, Qt, Signal
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

from flow3r.app.controller.session_state import ViewerOnly
from flow3r.app.visualization.source_widget import SourceWidget
from flow3r.app.visualization.visualizer_widget import VisualizerWidget
from flow3r.app.widgets.recording_controls_widget import RecordingControlsWidget
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.core.visualization.abc.visualizer_type import IVisualizerType


@dataclass
class _RecordingControlsWidgetEntry:
    widget: RecordingControlsWidget
    container: QWidget          # permanent zero-margin slot in _bottom_widget layout
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
        self._group_order: List[str] = []
        # Active session ID per group, kept in sync with active_session_changed.
        # Used by _on_session_state_changed to filter out state updates for
        # non-active (e.g. finished) sessions.
        self._active_session_ids: Dict[str, Optional[str]] = {}

    def set_controller(self, controller):
        assert self._controller is None
        self._controller = controller
        self.source_snapshot_requested.connect(controller.send_source_snapshot)
        self.group_snapshot_requested.connect(controller.send_group_snapshot)
        controller.config_changed.connect(self._on_config_changed)
        controller.active_session_changed.connect(self._on_active_session_changed)
        controller.active_session_snapshot.connect(self._on_active_session_changed)
        controller.session_state_changed.connect(self._on_session_state_changed)

    @Slot(str, str, object)
    def _on_active_session_changed(self, group_id: str, session_id: str, state) -> None:
        """Cache the active session ID and update recording-controls location.

        Handles ``active_session_changed`` and ``active_session_snapshot``, both of
        which always carry the active session's state, so no filtering is needed.
        """
        self._active_session_ids[group_id] = session_id
        self._apply_recording_controls_location(group_id, state)

    @Slot(str, str, object)
    def _on_session_state_changed(self, group_id: str, session_id: str, state) -> None:
        """Update recording-controls location on any session state change.

        ``session_state_changed`` fires for all sessions including finished non-active
        ones.  The cached active session ID is used to ignore updates that are not for
        the currently active session, preventing a completing old recording from
        un-hiding a viewer-only group.
        """
        if session_id != self._active_session_ids.get(group_id):
            return
        self._apply_recording_controls_location(group_id, state)

    def _apply_recording_controls_location(self, group_id: str, state) -> None:
        """Hide controls for ViewerOnly groups; show at bottom for all other states.

        Skips groups whose widget is embedded in a source dock (``"source"`` location),
        since that placement is managed by the source-widget teardown path.
        """
        entry = self._recording_control_widgets.get(group_id)
        if entry is None or entry.location == "source":
            return
        if isinstance(state, ViewerOnly):
            self.set_recording_controls_widget_location(group_id, "hidden")
        else:
            self.set_recording_controls_widget_location(group_id, "bottom")

    @Slot(object)
    def _on_config_changed(self, config) -> None:
        self._group_order = list(config.all_groups.keys())
        self._reorder_containers()

    def _reorder_containers(self) -> None:
        """Re-sort group containers in _bottom_widget layout to match _group_order."""
        layout = self._bottom_widget.layout()
        for position, group_id in enumerate(self._group_order):
            entry = self._recording_control_widgets.get(group_id)
            if entry is None:
                continue
            current = layout.indexOf(entry.container)
            if current != -1 and current != position:
                layout.insertWidget(position, entry.container)

    @Slot(str, str, object)
    def add_source_handle(self, source_id: str, session_id: str, handle: IVisualizerHandle) -> None:
        if source_id not in self._source_handles:
            self._source_handles[source_id] = {}
        self._source_handles[source_id][session_id] = handle

    @Slot(str, str)
    def remove_source_handle(self, source_id: str, session_id: str) -> None:
        self._source_handles[source_id].pop(session_id, None)

    @Slot(str, str, str, object)
    def add_visualizer_handle(self, group_id: str, widget_id: str, session_id: str, handle: IVisualizerHandle) -> None:
        if (group_id, widget_id) not in self._visualizer_handles:
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
                rc_widget = widget.recording_controls_widget
                # Put the recording controls widget back into its container slot.
                for entry in self._recording_control_widgets.values():
                    if entry.widget is rc_widget:
                        entry.container.layout().addWidget(rc_widget)
                        entry.container.setVisible(False)
                        rc_widget.setVisible(False)
                        entry.location = "hidden"
                        entry.source_id = None
                        break
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
        widget.set_recording_number.connect(self._controller.set_recording_number)
        widget.edit_group.connect(self._main_window._edit_group)
        widget.set_placeholder_values.connect(self._main_window._set_group_placeholders)
        widget.open_placeholder_dialog_for_start.connect(self._main_window._fill_and_start_recording)
        widget.active_session_requested.connect(self._controller.send_active_session_snapshot)
        self._controller.group_snapshot.connect(widget.group_changed)
        self._controller.group_changed.connect(widget.group_changed)
        self._controller.active_session_snapshot.connect(widget.set_active_session)
        self._controller.active_session_changed.connect(widget.set_active_session)
        self._controller.session_state_changed.connect(widget.set_session_state)
        self._main_window.auto_start_requested.connect(widget.on_auto_start_requested)
        widget.request_active_session()

        self.group_snapshot_requested.emit(group_id)

        # Create a permanent zero-margin container slot for this group.
        container = QWidget(self._bottom_widget)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(widget)
        container.setVisible(False)

        entry = _RecordingControlsWidgetEntry(widget, container)
        self._recording_control_widgets[group_id] = entry

        # Append then sort — _group_order already contains this group_id.
        self._bottom_widget.layout().addWidget(container)
        self._reorder_containers()

    @Slot(str)
    def remove_recording_controls_widget(self, group_id: str) -> None:
        self._active_session_ids.pop(group_id, None)
        entry = self._recording_control_widgets.pop(group_id, None)
        if entry:
            if entry.location == "source":
                old_source_widget = self._source_widgets[entry.source_id]
                old_source_widget.set_recording_controls_widget(None)
                entry.widget.deleteLater()
            # Remove the container (and widget if still inside it) from the layout.
            self._bottom_widget.layout().removeWidget(entry.container)
            entry.container.deleteLater()

    @Slot(str, str, object)
    def set_recording_controls_widget_location(self, group_id: str, location: Literal["hidden", "source", "bottom"], source_id: Optional[str] = None) -> None:
        entry = self._recording_control_widgets[group_id]
        if location == "source":
            assert source_id is not None

        if entry.location == location and entry.source_id == source_id:
            return

        # ── Tear down current location ────────────────────────────────────────
        if entry.location == "source":
            old_source_widget = self._source_widgets[entry.source_id]
            old_source_widget.set_recording_controls_widget(None)
            # Return widget to its container so visibility changes below are coherent.
            entry.container.layout().addWidget(entry.widget)

        # ── Set up new location ───────────────────────────────────────────────
        if location == "source":
            entry.container.layout().removeWidget(entry.widget)
            entry.container.setVisible(False)
            source_widget = self._source_widgets[source_id]
            source_widget.set_recording_controls_widget(entry.widget)
            entry.widget.setVisible(True)
            entry.widget.hide_group_name()
            entry.location = location
            entry.source_id = source_id
        elif location == "bottom":
            entry.widget.setVisible(True)
            entry.widget.show_group_name()
            entry.container.setVisible(True)
            entry.location = location
            entry.source_id = None
        elif location == "hidden":
            entry.widget.setVisible(False)
            entry.container.setVisible(False)
            entry.location = location
            entry.source_id = None
