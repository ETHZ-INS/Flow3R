from pathlib import Path
from typing import List, Optional

import reactivex as rx
from reactivex import operators as ops
from reactivex.disposable import CompositeDisposable

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription
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
            self._widget_handle = app_context.widget_service.get_visualizer_handle("my_video")

    def build(self, app_context: IAppContext, sources: List[IStream]) -> PipelineSubscription:
        assert len(sources) == 1
        source = sources[0]

        video_writer_sink = VideoWriterSink(Path(self._config.video_file))
        visualizer_sink = VisualizerSink(app_context.widget_service, "my_video")

        shared_source = Stream(source.descriptor, source.observable.pipe(ops.share()))
        video_writer_sub = video_writer_sink.subscribe(shared_source)
        visualizer_sub = visualizer_sink.subscribe(shared_source)

        disposable = CompositeDisposable(video_writer_sub, visualizer_sub)
        primary_done = rx.merge(video_writer_sub.done, visualizer_sub.done).pipe(ops.take(1))
        return PipelineSubscription(disposable, primary_done)

    def dispose(self):
        if self._widget_handle:
            self._widget_handle.dispose()
