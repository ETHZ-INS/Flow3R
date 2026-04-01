from pathlib import Path
from typing import Optional, Dict

import reactivex as rx
from py3r.media.video.ffmpeg_video_file_writer import FFmpegVideoFileWriter
from reactivex import operators as ops
from reactivex.disposable import CompositeDisposable
from reactivex.scheduler import EventLoopScheduler

from flow3r.core.api.app.session_context import ISessionContext
from flow3r.core.pipeline.abc.pipeline import PipelineSubscription, PipelineBase, PreviewSubscription
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig
from flow3r.plugins.core.node.video_writer_sink import VideoWriterSink
from flow3r.plugins.core.typing.video import VideoFormat


def video_writer_factory(segment_file: Path, desc: VideoFormat):
    return FFmpegVideoFileWriter(segment_file, desc.size, desc.fps, grayscale=desc.fmt=="mono8", quality="low")


class RecordVideoPipeline(PipelineBase[RecordVideoConfig]):
    def __init__(self):
        self._config: Optional[RecordVideoConfig] = None

        self._main_scheduler = EventLoopScheduler()
        self._writer_scheduler = EventLoopScheduler()

    def configure(self, session_context: ISessionContext, config: RecordVideoConfig):
        self._config = config

    def preview(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PreviewSubscription:
        return PreviewSubscription(CompositeDisposable(), rx.from_list([None]))

    def build(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PipelineSubscription:
        print(self._config.video_file)
        print(Path(self._config.video_file).absolute())
        source = sources["Video"]
        video_writer_sink = VideoWriterSink(Path(self._config.video_file), factory=video_writer_factory)

        shared_source = Stream(source.format, source.data.pipe(ops.observe_on(self._main_scheduler), ops.share()))
        video_writer_stream = Stream(source.format, shared_source.data.pipe(ops.observe_on(self._writer_scheduler)))

        video_writer_sub = video_writer_sink.subscribe(video_writer_stream)

        disposable = CompositeDisposable(video_writer_sub)
        primary_done = rx.zip(video_writer_sub.done).pipe(ops.take(1))
        return PipelineSubscription(disposable, primary_done)

    def dispose(self):
        pass
