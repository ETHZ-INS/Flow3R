from typing import Callable, Optional, Protocol, Any

from py3r.media.types import VideoFrame

from aaaflow3r.core.api.app.widget_service import IWidgetService
from aaaflow3r.core.streaming.abc.sink import Sink
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.plugins.core.typing.video import VideoFormat


class VisualizerSink(Sink[Any, Any]):
    def __init__(self, widget_service: IWidgetService, widget_id: str):
        super().__init__()
        self._widget_service = widget_service
        self._widget_id = widget_id
        self._visualizer_handle: Optional[IVisualizerHandle] = None

    def setup(self, desc: VideoFormat) -> None:
        self._visualizer_handle = self._widget_service.get_visualizer_handle(self._widget_id)
        self._visualizer_handle._inner._on_desc(desc)

    def on_next(self, item: VideoFrame) -> None:
        assert self._visualizer_handle is not None
        self._visualizer_handle._inner._on_next(item)

    def on_error(self, exc: Exception) -> None:
        self._visualizer_handle._inner._on_error(exc)

    def on_completed(self) -> None:
        self._visualizer_handle._inner._on_completed()

    def cleanup(self) -> None:
        if self._visualizer_handle:
            self._visualizer_handle.dispose()
            self._visualizer_handle = None
