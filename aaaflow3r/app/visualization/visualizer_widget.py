from typing import Optional

from PySide6.QtWidgets import QDockWidget, QWidget

from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


class VisualizerWidget(QDockWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._handle: Optional[IVisualizerHandle] = None
        self._visualizer: Optional[QWidget] = None

    def set_handle(self, handle: IVisualizerHandle):
        self._handle = handle
        if self._visualizer:
            self._visualizer.set_handle(handle)

    def set_visualizer(self, visualizer: QWidget):
        if self._visualizer:
            self._visualizer.set_handle(None)
            self._visualizer.setParent(None)

        self._visualizer = visualizer
        if self._visualizer:
            self.setWidget(self._visualizer)
            self._visualizer.set_handle(self._handle)
