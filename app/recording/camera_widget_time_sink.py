import numpy as np
from rx.core import Observer

from app.widgets.camera_widget import CameraWidget
from app.widgets.recording_controls_widget import RecordingControlsWidget


class CameraWidgetTimeSink(Observer):
    def __init__(self, widget: RecordingControlsWidget):
        super().__init__()
        self.widget = widget
        self._sub = None

    def on_next(self, frame: tuple[int, float, np.ndarray]):
        if self.widget is None:
            return
        _, ts, _ = frame
        self.widget.set_recording_time.future(ts)

    def on_error(self, err):
        print(f"[CameraWidgetTimeSink] error: {err}")
        import traceback
        traceback.print_exc()
        self.dispose()

    def on_completed(self):
        print("[CameraWidgetTimeSink] completed")
        self.dispose()

    def attach(self, upstream):
        """Subscribe to an Observable and remember the disposable."""
        if self._sub:
            self._sub.dispose()
        self._sub = upstream.subscribe(self)
        return self._sub

    def dispose(self):
        print("[CameraWidgetTimeSink] disposing...")
        if self._sub:
            self._sub.dispose()
            self._sub = None
        self.widget = None
