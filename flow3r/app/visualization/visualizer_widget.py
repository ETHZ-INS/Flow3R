from typing import Optional, Any, List

from PySide6.QtCore import Slot, QPoint
from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QDockWidget, QWidget, QMenu, QVBoxLayout

from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.core.visualization.abc.visualizer_type import IVisualizerType


class VisualizerWidget(QDockWidget):
    def __init__(self, visualizers: List[IVisualizerType], parent = None):
        super().__init__(parent)

        self._visualizers = visualizers

        self.content = QWidget(self)
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.content.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.content.customContextMenuRequested.connect(self._show_context_menu)

        self.setWidget(self.content)

        self.visualizer_frame = QWidget(self)
        visualizer_frame_layout = QVBoxLayout(self.visualizer_frame)
        visualizer_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.content.layout().addWidget(self.visualizer_frame)

        self._descriptor: Any = None

        self._manually_set_visualizer = False
        self._current_visualizer_name = None
        self._handle: Optional[IVisualizerHandle] = None
        self._visualizer: Optional[QWidget] = None

        self.visibilityChanged.connect(self._visibility_changed)

    def set_handle(self, handle: Optional[IVisualizerHandle[Any, Any]]):
        if self._handle:
            self._handle.desc_changed.disconnect(self._desc_changed)

        self._handle = handle
        if self._visualizer:
            self._visualizer.set_handle(handle)

        if self._handle:
            self._handle.desc_changed.connect(self._desc_changed)

            if self._handle.desc:
                self._desc_changed(self._handle.desc)

    def set_visualizer(self, name: str, visualizer: QWidget, manual: bool = False):
        self.visualizer_frame.layout().children().clear()

        if self._visualizer:
            self._visualizer.set_handle(None)
            self._visualizer.setParent(None)

        self._manually_set_visualizer = manual
        self._current_visualizer_name = name
        self._visualizer = visualizer

        if self._visualizer:
            self.visualizer_frame.layout().addWidget(self._visualizer)
            self._visualizer.set_handle(self._handle)

    @Slot(object)
    def _desc_changed(self, desc: Any):
        self._descriptor = desc
        if self._manually_set_visualizer:
            return
        for visualizer_type in self._visualizers:
            if visualizer_type.accepts(desc):
                self.set_visualizer(visualizer_type.name, visualizer_type.widget_factory())
                break

    @Slot(object)
    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)

        # Build actions from dict
        for visualizer_type in self._visualizers:
            if not visualizer_type.accepts(self._descriptor):
                continue

            action = QAction(visualizer_type.name, menu)
            action.setCheckable(True)
            action.setChecked(visualizer_type.name == self._current_visualizer_name)

            # Optional: disable selecting the already-active one
            if visualizer_type.name == self._current_visualizer_name:
                action.setEnabled(False)

            # Capture cls in default arg
            action.triggered.connect(lambda _=False, vt=visualizer_type: self.set_visualizer(vt.name, vt.widget_factory(), manual=True))
            menu.addAction(action)

        menu.addSeparator()

        clear_action = QAction("No visualization", menu)
        clear_action.setEnabled(self._current_visualizer_name is not None)
        clear_action.triggered.connect(lambda: self.set_visualizer(None, None, manual=True))
        menu.addAction(clear_action)

        menu.addSeparator()

        visualizer_menu = menu.addMenu("Visualizer Settings")
        self._populate_visualizer_submenu(visualizer_menu)

        if visualizer_menu.isEmpty():
            visualizer_menu.setEnabled(False)

        # Map the position correctly depending on who emitted the signal
        sender = self.sender()
        if isinstance(sender, QWidget):
            global_pos = sender.mapToGlobal(pos)
        else:
            global_pos = self.mapToGlobal(pos)

        menu.exec(global_pos)

    def _populate_visualizer_submenu(self, menu: QMenu) -> None:
        if self._visualizer is None:
            return

        populate = getattr(self._visualizer, "populate_context_menu", None)
        if callable(populate):
            populate(menu)

    def _visibility_changed(self, visible: bool):
        self.visualizer_frame.setVisible(visible)
