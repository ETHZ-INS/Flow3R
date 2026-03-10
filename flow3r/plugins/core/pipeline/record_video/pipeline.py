from pathlib import Path
from typing import List, Optional, Dict

import reactivex as rx
from reactivex import operators as ops
from reactivex.disposable import CompositeDisposable
from reactivex.scheduler import EventLoopScheduler

from flow3r.core.api.app.session_context import ISessionContext
from flow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription, PipelineBase
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig
from flow3r.plugins.core.node.video_writer_sink import VideoWriterSink


class RecordVideoPipeline(PipelineBase[RecordVideoConfig]):
    def __init__(self):
        self._widget_handle: Optional[IVisualizerHandle] = None
        self._config: Optional[RecordVideoConfig] = None

        self._main_scheduler = EventLoopScheduler()
        self._writer_scheduler = EventLoopScheduler()

    def configure(self, session_context: ISessionContext, config: RecordVideoConfig):
        self._config = config

    def build(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PipelineSubscription:
        source = sources["Video"]

        video_writer_sink = VideoWriterSink(Path(self._config.video_file))
        #visualizer_sink = VisualizerSink(session_context.widget_service, "Video Preview")

        shared_source = Stream(source.descriptor, source.observable.pipe(ops.observe_on(self._main_scheduler), ops.share()))
        video_writer_stream = Stream(source.descriptor, shared_source.observable.pipe(ops.observe_on(self._writer_scheduler)))

        video_writer_sub = video_writer_sink.subscribe(video_writer_stream)
        #visualizer_sub = visualizer_sink.subscribe(shared_source)

        disposable = CompositeDisposable(video_writer_sub)
        primary_done = rx.zip(video_writer_sub.done).pipe(ops.take(1))
        return PipelineSubscription(disposable, primary_done)

    def dispose(self):
        pass
