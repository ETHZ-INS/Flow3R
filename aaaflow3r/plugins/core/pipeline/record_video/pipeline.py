from pathlib import Path
from typing import List, Any, Optional

from reactivex import operators as ops

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.pipeline.abc.pipeline import IPipeline
from aaaflow3r.core.streaming.abc.stream import IStream
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.core.visualization.visualizer_sink import VisualizerSink
from aaaflow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig
from aaaflow3r.plugins.core.util.video_writer import VideoWriterSink


class RecordVideoPipeline(IPipeline[RecordVideoConfig]):
    def __init__(self):
        self._widget_handle: Optional[IVisualizerHandle] = None
        self._config: Optional[RecordVideoConfig] = None

    def configure(self, app_context: IAppContext, config: RecordVideoConfig):
        self._config = config
        if not self._widget_handle:
            self._widget_handle = app_context.widget_service.get_visualizer_handle("Video", "my_video", "preview")

    def build(self, app_context: IAppContext, sources: List[IStream]) -> Any:
        assert len(sources) == 1
        source = sources[0]

        video_writer_sink = VideoWriterSink(Path(self._config.video_file))
        visualizer_sink = VisualizerSink(app_context.widget_service, "Video", "my_video", "live")

        shared_source = Stream(source.descriptor, source.observable.pipe(ops.share()))
        video_writer_sink.subscribe(shared_source)
        visualizer_sink.subscribe(shared_source)

    def dispose(self):
        if self._widget_handle:
            self._widget_handle.dispose()
