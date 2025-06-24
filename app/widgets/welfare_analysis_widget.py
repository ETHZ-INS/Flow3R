from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDockWidget

from rx import operators as ops
from rx.scheduler import ThreadPoolScheduler

from app.layout.welfare_analysis_widget import Ui_WelfareAnalysisWidget


class WelfareAnalysisWidget(Ui_WelfareAnalysisWidget, QDockWidget):
    update_signal = Signal(float)

    def __init__(self):
        super(WelfareAnalysisWidget, self).__init__()

        self.setupUi(self)

        self._worker = ThreadPoolScheduler(1)
        self._sub = None

        self.update_signal.connect(self.update_analysis)

    def on_next(self, distance_travelled: float):
        self.update_signal.emit(distance_travelled)

    def on_error(self, err):
        print(f"[CameraWidget] error: {err}")

    def on_completed(self):
        print("[CameraWidget] completed")

    def update_analysis(self, distance_travelled: float):
        self.label.setText(f"Distance Travelled: {distance_travelled:.2f}")

    def attach(self, obs):
        """
        Subscribe to a heat-map stream.
        `scheduler` lets you override which Qt thread receives the images.
        """
        self.dispose()

        self._sub = (
            obs.pipe(
                ops.observe_on(self._worker),
            )
            .subscribe(self)
        )
        return self._sub

    def dispose(self):
        if self._sub:
            self._sub.dispose()
            self._sub = None
