import tempfile
from pathlib import Path
from typing import Optional, Dict

import reactivex as rx
from reactivex import operators as ops
from reactivex.scheduler import EventLoopScheduler

from flow3r.core.pipeline.abc.pipeline import ConfigureContext, PreviewContext, PipelineContext, PipelineBase
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.node.audio_writer_transform import AudioWriterTransform
from flow3r.plugins.core.node.video_audio_muxer import VideoAudioMuxerSink
from flow3r.plugins.core.node.video_writer_transform import VideoWriterTransform
from flow3r.plugins.core.pipeline.record_video_with_audio.config import RecordVideoWithAudioConfig


class RecordVideoWithAudioPipeline(PipelineBase[RecordVideoWithAudioConfig]):
    def __init__(self):
        self._config: Optional[RecordVideoWithAudioConfig] = None

        self._main_scheduler = EventLoopScheduler()
        self._writer_scheduler = EventLoopScheduler()

    def configure(self, context: ConfigureContext[RecordVideoWithAudioConfig]) -> None:
        self._config = context.config

    def preview(self, context: PreviewContext[RecordVideoWithAudioConfig], sources: Dict[str, IStream]) -> None:
        context.register_done(rx.from_list([None]))

    def build(self, context: PipelineContext[RecordVideoWithAudioConfig], sources: Dict[str, IStream]) -> None:
        video_source = sources["Video"]
        audio_source = sources["Audio"]

        temp_dir = Path(tempfile.mkdtemp())
        temp_video_file = temp_dir / "video.mkv"
        temp_audio_file = temp_dir / "audio.flac"

        video_writer_transform = VideoWriterTransform(temp_video_file)
        audio_writer_transform = AudioWriterTransform(temp_audio_file)
        video_audio_muxer_sink = VideoAudioMuxerSink(Path(context.config.video_file))

        shared_video_source = Stream(video_source.format, video_source.data.pipe(ops.observe_on(self._main_scheduler), ops.share()))

        video_writer_stream = Stream(shared_video_source.format, shared_video_source.data.pipe(ops.observe_on(self._writer_scheduler)))
        audio_writer_stream = Stream(audio_source.format, audio_source.data.pipe(ops.observe_on(self._writer_scheduler)))

        video_file_stream = video_writer_transform.pipe(video_writer_stream)
        audio_file_stream = audio_writer_transform.pipe(audio_writer_stream)

        video_audio_muxer_stream = Stream(
            (video_file_stream.format, audio_file_stream.format),
            rx.zip(video_file_stream.data, audio_file_stream.data)
        )
        muxer_sub = video_audio_muxer_sink.subscribe(video_audio_muxer_stream)

        context.register_primary_done(muxer_sub.done)
        context.add_disposable(muxer_sub.disposable)

    def dispose(self):
        pass
