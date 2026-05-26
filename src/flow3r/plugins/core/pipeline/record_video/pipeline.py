from pathlib import Path
from typing import Optional, Dict

import reactivex as rx
from py3r.media.video.ffmpeg_video_file_writer import FFmpegVideoFileWriter
from reactivex import operators as ops
from reactivex.scheduler import EventLoopScheduler
from flow3r.core.pipeline.abc.pipeline import ConfigureContext, PreviewContext, PipelineContext, PipelineBase
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig
from flow3r.plugins.core.node.video_writer_sink import VideoWriterSink
from flow3r.plugins.core.pipeline.util.pyav_video_file_writer import PyAVVideoFileWriter
from flow3r.plugins.core.typing.video import VideoFormat


def video_writer_factory(quality: str):
    def _factory(segment_file: Path, desc: VideoFormat):
        return PyAVVideoFileWriter(segment_file, desc.size, desc.fps, grayscale=desc.fmt=="mono8", quality=quality)
    return _factory


class RecordVideoPipeline(PipelineBase[RecordVideoConfig]):
    def __init__(self):
        self._config: Optional[RecordVideoConfig] = None

        self._writer_scheduler = EventLoopScheduler()

    def configure(self, context: ConfigureContext[RecordVideoConfig]) -> None:
        self._config = context.config

    def preview(self, context: PreviewContext[RecordVideoConfig], sources: Dict[str, IStream]) -> None:
        context.register_done(rx.from_list([None]))

    def build(self, context: PipelineContext[RecordVideoConfig], sources: Dict[str, IStream]) -> None:
        source = sources["Video"]
        video_writer_sink = VideoWriterSink(Path(context.config.video_file), factory=video_writer_factory(context.config.video_quality))

        video_writer_stream = Stream(source.format, source.data.pipe(ops.observe_on(self._writer_scheduler)))
        video_writer_sub = video_writer_sink.subscribe(video_writer_stream)

        context.register_primary_done(video_writer_sub.done)
        context.add_disposable(video_writer_sub.disposable)

    def dispose(self):
        pass
