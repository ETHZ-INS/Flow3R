from typing import Callable, Optional, Protocol, Any

from py3r.media.types import VideoFrame

from flow3r.core.api.app.widget_service import IWidgetService
from flow3r.core.streaming.abc.sink import Sink
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.plugins.core.typing.video import VideoFormat


class VisualizerSink(Sink[Any, Any]):
    def __init__(self, widget_service: IWidgetService, widget_type: str, widget_id: str, session_id: str):
        super().__init__()
        self._widget_service = widget_service
        self._widget_type = widget_type
        self._widget_id = widget_id
        self._session_id = session_id
        self._visualizer_handle: Optional[IVisualizerHandle] = None

    def setup(self, desc: VideoFormat) -> None:
        self._visualizer_handle = self._widget_service.get_visualizer_handle(self._widget_type, self._widget_id, self._session_id)

    def on_next(self, item: VideoFrame) -> None:
        assert self._writer is not None
        self._writer.write(item)

    def cleanup(self) -> None:
        if self._visualizer_handle:
            self._visualizer_handle.dispose()
            self._visualizer_handle = None
