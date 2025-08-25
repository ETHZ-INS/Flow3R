import numpy as np
from PySide6.QtCore import Signal, QObject
from rx.core import Observer

from app.widgets.camera_widget import CameraWidget


class QObserverMeta(type(Observer), type(QObject)):
    """Metaclass to combine Observer and QObject functionality."""
    pass


class CameraWidgetImageSink(QObject):
    error = Signal(str)

    def __init__(self, widget: CameraWidget):
        super().__init__()
        self.widget = widget
        self._sub = None

    def on_next(self, frame: tuple[int, float, np.ndarray]):
        if self.widget is None:
            return
        _, _, image = frame
        self.widget.set_image(image)

    def on_error(self, err):
        print(f"[CameraWidgetImageSink] error: {err}")
        import traceback
        traceback.print_exc()
        self.dispose()
        self.error.emit(str(err))

    def on_completed(self):
        print("[CameraWidgetImageSink] completed")
        self.dispose()

    def attach(self, upstream):
        """Subscribe to an Observable and remember the disposable."""
        if self._sub:
            self._sub.dispose()
        self._sub = upstream.subscribe(self)
        return self._sub

    def dispose(self):
        print("[CameraWidgetImageSink] disposing...")
        if self._sub:
            self._sub.dispose()
            self._sub = None
        self.widget = None
