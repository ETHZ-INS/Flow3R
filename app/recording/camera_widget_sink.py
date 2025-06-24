import rx


class CameraWidgetSink(rx.core.Observer):
    """
    RxPY Observer that shows frames in an OpenCV window.

    Usage
    -----
    sink = CameraWidgetSink(main_window, camera_id)
    subscription = some_observable.subscribe(sink)   # start preview
    ...
    subscription.dispose()                           # or sink.dispose()
    """

    def __init__(self, gui, camera_id: str):
        super().__init__()
        self.gui = gui
        self.camera_id = camera_id
        self._subscription = None

    # -------------------------------- Observer API ------------------
    def on_next(self, value):
        frame = value
        self.gui.camera_widgets[self.camera_id].set_image(frame)

    def on_error(self, err):
        print(f"[CameraWidgetSink] error: {err}")
        self._cleanup()

    def on_completed(self):
        print("[CameraWidgetSink] completed")
        self._cleanup()

    # ---------------------------------------------------------------
    def attach(self, upstream: rx.Observable):
        """Convenience helper: subscribe and remember the Disposable."""
        self._subscription = upstream.subscribe(self)
        return self._subscription

    def dispose(self):
        """Dispose the subscription manually, if needed."""
        if self._subscription:
            self._subscription.dispose()
            self._subscription = None
        self._cleanup()

    # ------------------------- internals ---------------------------
    def _cleanup(self):
        pass