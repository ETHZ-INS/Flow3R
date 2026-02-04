from typing import Optional, Any

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDockWidget, QWidget

from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.plugins.core.typing.audio import AudioFormat
from aaaflow3r.plugins.core.typing.video import VideoFormat
from aaaflow3r.plugins.core.visualization.audio.spectogram.widget import SpectrogramWidget
from aaaflow3r.plugins.core.visualization.video.widget import VideoWidget


class VisualizerWidget(QDockWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._handle: Optional[IVisualizerHandle] = None
        self._visualizer: Optional[QWidget] = None
        print("Created visualizer widget")

    def set_handle(self, handle: Optional[IVisualizerHandle[Any, Any]]):
        if self._handle:
            self._handle.desc_changed.disconnect(self._desc_changed)

        self._handle = handle
        if self._visualizer:
            self._visualizer.set_handle(handle)

        if self._handle:
            print("Connecting desc changed")
            self._handle.desc_changed.connect(self._desc_changed)
            self._desc_changed(self._handle.desc)
            print("OK")

    def set_visualizer(self, visualizer: QWidget):
        if self._visualizer:
            self._visualizer.set_handle(None)
            self._visualizer.setParent(None)

        self._visualizer = visualizer
        if self._visualizer:
            self.setWidget(self._visualizer)
            self._visualizer.set_handle(self._handle)

    @Slot(object)
    def _desc_changed(self, desc: Optional[Any]):
        self.desc = desc
        if isinstance(desc, VideoFormat):
            if not isinstance(self._visualizer, VideoWidget):
                print("Setting video widget")
                self.set_visualizer(VideoWidget())
                print("OK")
        elif isinstance(desc, AudioFormat):
            if not isinstance(self._visualizer, SpectrogramWidget):
                self.set_visualizer(SpectrogramWidget())
        else:
            self.set_visualizer(None)
