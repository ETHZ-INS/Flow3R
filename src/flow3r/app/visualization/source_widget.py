from typing import Optional, Any, List

from PySide6.QtCore import Signal, Qt, Slot, QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QDockWidget, QMenu, QSizePolicy

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.widgets.recording_controls_widget import RecordingControlsWidget
from flow3r.app.config.source_config import SourceConfig
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.core.visualization.abc.visualizer_type import IVisualizerType


class SourceWidget(QDockWidget):
    edit_source = Signal(str)
    setup_source = Signal(str)

    group_snapshot_requested = Signal(str)

    def __init__(self, visualizers: List[IVisualizerType], source_id: str, parent=None):
        super().__init__(parent)

        self._visualizers = visualizers

        self.source_id = source_id
        self.setWindowTitle(source_id)

        self.source_name: Optional[str] = None
        self.group_id: Optional[str] = None
        self.group_name: Optional[str] = None

        self.dock_widget_content = QWidget(self)

        self.dock_widget_content.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.dock_widget_content.customContextMenuRequested.connect(self._show_context_menu)

        self.setWidget(self.dock_widget_content)

        layout = QVBoxLayout(self.dock_widget_content)
        layout.setContentsMargins(0, 0, 0, 0)

        self.content = QStackedWidget(self.dock_widget_content)
        layout.addWidget(self.content)

        self.bottom_widget = QWidget(self.dock_widget_content)
        bottom_layout = QVBoxLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_widget.setVisible(False)
        layout.addWidget(self.bottom_widget)

        self.lbl_error = QLabel(self, text="Error")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.lbl_error.setMinimumWidth(0)
        self.lbl_error.linkActivated.connect(self._on_link_activated)
        self.content.addWidget(self.lbl_error)

        self.visualizer_widget_holder: QWidget = QWidget(self.dock_widget_content)
        visualizer_layout = QVBoxLayout(self.visualizer_widget_holder)
        visualizer_layout.setContentsMargins(0, 0, 0, 0)
        self.content.addWidget(self.visualizer_widget_holder)

        self._format: Any = None

        self._manually_set_visualizer = False
        self._current_visualizer_type = None
        self._handle: Optional[IVisualizerHandle] = None
        self._visualizer: Optional[QWidget] = None

        self.recording_controls_widget: Optional[RecordingControlsWidget] = None

    def set_handle(self, handle: Optional[IVisualizerHandle[Any, Any]]):
        if self._handle:
            self._handle.format_changed.disconnect(self._format_changed)
            self._handle.error_changed.disconnect(self._error)

        self._handle = handle
        if self._visualizer:
            self._visualizer.set_handle(handle)

        if self._handle:
            self._handle.format_changed.connect(self._format_changed)
            self._handle.error_changed.connect(self._error)
            self._format_changed(self._handle.format)
            self._error(self._handle.error)

    def set_visualizer(self, visualizer_type: Optional[IVisualizerType], manual: bool = False):
        if self._visualizer:
            self._visualizer.set_handle(None)
            self.visualizer_widget_holder.layout().removeWidget(self._visualizer)
            self._visualizer.setParent(None)

        self._manually_set_visualizer = manual
        self._current_visualizer_type = visualizer_type
        if visualizer_type is not None:
            self._visualizer = visualizer_type.widget_factory(self.visualizer_widget_holder)
            self.visualizer_widget_holder.layout().addWidget(self._visualizer)
            self._visualizer.set_handle(self._handle)

    def set_recording_controls_widget(self, widget: Optional[RecordingControlsWidget]):
        if self.recording_controls_widget:
            self.bottom_widget.layout().removeWidget(self.recording_controls_widget)

        self.recording_controls_widget = widget

        if widget:
            self.bottom_widget.setVisible(True)
            self.bottom_widget.layout().addWidget(widget)
        else:
            self.bottom_widget.setVisible(False)

    def source_changed(self, source_config: SourceConfig):
        if self.source_id != source_config.id:
            return

        self.source_name = source_config.name
        if source_config.group_id != self.group_id:
            self.group_id = source_config.group_id
            self.group_name = None
            if self.group_id is not None:
                self.group_snapshot_requested.emit(source_config.group_id)

        self._update_window_title()

    def group_changed(self, group_config: GroupConfig):
        if self.group_id != group_config.id:
            return

        self.group_name = group_config.name
        self._update_window_title()

    def _update_window_title(self):
        source_name = self.source_name or self.source_id
        if self.group_name:
            self.setWindowTitle(f"{source_name} ({self.group_name})")
        else:
            self.setWindowTitle(source_name)

    @Slot(object)
    def _format_changed(self, fmt: Any):
        self._format = fmt
        if fmt is None or self._manually_set_visualizer:
            return

        if self._current_visualizer_type is not None:
            if self._current_visualizer_type.accepts(fmt):
                return

        for visualizer_type in self._visualizers:
            if visualizer_type.accepts(fmt):
                self.set_visualizer(visualizer_type)
                break

    @Slot(object)
    def _error(self, error: Optional[Exception]):
        if error:
            message = str(error)
            message = message.replace("\n", "<br>")
            message += "<br><a href=\"edit\">Edit Source</a>"
            message += "<br><a href=\"retry\">Retry</a>"
            self.lbl_error.setText(message)
            self.content.setCurrentIndex(0)
        else:
            self.lbl_error.setText("")
            self.content.setCurrentIndex(1)

    def _on_link_activated(self, link: str):
        """Handle link activation in the camera message."""
        if link == "retry":
            self.lbl_error.setText("Retrying...")
            self._setup_source()
        elif link == "edit":
            self._edit_source()

    def _setup_source(self):
        self.setup_source.emit(self.source_id)

    def _edit_source(self):
        self.edit_source.emit(self.source_id)

    @Slot(object)
    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)

        # Build actions from dict
        for visualizer_type in self._visualizers:
            if not visualizer_type.accepts(self._format):
                continue

            action = QAction(visualizer_type.name, menu)
            action.setCheckable(True)
            action.setChecked(visualizer_type.name == self._current_visualizer_type)

            # Optional: disable selecting the already-active one
            if visualizer_type.name == self._current_visualizer_type:
                action.setEnabled(False)

            # Capture cls in default arg
            action.triggered.connect(lambda _=False, vt=visualizer_type: self.set_visualizer(vt, manual=True))
            menu.addAction(action)

        menu.addSeparator()

        clear_action = QAction("No Visualization", menu)
        clear_action.setEnabled(self._current_visualizer_type is not None)
        clear_action.triggered.connect(lambda: self.set_visualizer(None, manual=True))
        menu.addAction(clear_action)

        menu.addSeparator()

        edit_action = QAction("Edit Source", menu)
        edit_action.triggered.connect(self._edit_source)
        menu.addAction(edit_action)

        # Map the position correctly depending on who emitted the signal
        sender = self.sender()
        if isinstance(sender, QWidget):
            global_pos = sender.mapToGlobal(pos)
        else:
            global_pos = self.mapToGlobal(pos)

        menu.exec(global_pos)
