from typing import Optional, TypeVar


from flow3r.core.api.app.widget_service import IWidgetService
from flow3r.core.streaming.abc.sink import Sink
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class VisualizerSink(Sink[TDesc, TData]):
    def __init__(self, widget_service: IWidgetService, widget_id: str):
        super().__init__()
        self._widget_service = widget_service
        self._widget_id = widget_id

        self._visualizer_handle: Optional[IVisualizerHandle] = None

    def setup(self, fmt: TDesc) -> None:
        self._visualizer_handle = self._widget_service.get_visualizer_handle(self._widget_id)
        assert self._visualizer_handle is not None
        self._visualizer_handle.set_format(fmt)

    def on_next(self, item: TData) -> None:
        assert self._visualizer_handle is not None
        self._visualizer_handle.set_item(item)

    def on_error(self, exc: Exception) -> None:
        assert self._visualizer_handle is not None
        self._visualizer_handle.set_error(exc)

    def on_completed(self) -> None:
        assert self._visualizer_handle is not None
        self._visualizer_handle.set_completed(True)

    def cleanup(self) -> None:
        if self._visualizer_handle:
            self._visualizer_handle.dispose()
            self._visualizer_handle = None
