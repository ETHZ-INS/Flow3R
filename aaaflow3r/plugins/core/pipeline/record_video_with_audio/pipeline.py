import tempfile
from concurrent.futures import Future
from pathlib import Path
from typing import List, Optional

import reactivex as rx
from reactivex import operators as ops
from reactivex.disposable import CompositeDisposable
from reactivex.scheduler import EventLoopScheduler

from aaaflow3r.core.api.app.session_context import ISessionContext
from aaaflow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription
from aaaflow3r.core.streaming.abc.stream import IStream
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.core.visualization.visualizer_sink import VisualizerSink
from aaaflow3r.plugins.core.node.audio_writer_transform import AudioWriterTransform
from aaaflow3r.plugins.core.node.video_audio_muxer import VideoAudioMuxerSink
from aaaflow3r.plugins.core.node.video_writer_transform import VideoWriterTransform
from aaaflow3r.plugins.core.pipeline.record_video_with_audio.config import RecordVideoWithAudioConfig


class RecordVideoWithAudioPipeline(IPipeline[RecordVideoWithAudioConfig]):
    def __init__(self):
        self._widget_handle: Optional[IVisualizerHandle] = None
        self._config: Optional[RecordVideoWithAudioConfig] = None

        self._main_scheduler = EventLoopScheduler()
        self._writer_scheduler = EventLoopScheduler()

    def configure(self, session_context: ISessionContext, config: RecordVideoWithAudioConfig):
        self._config = config
        if not self._widget_handle:
            self._widget_handle = session_context.widget_service.get_visualizer_handle("Video Preview")

    def build(self, session_context: ISessionContext, sources: List[IStream]) -> PipelineSubscription:
        assert len(sources) == 2
        video_source = sources[0]
        audio_source = sources[1]

        temp_dir = Path(tempfile.mkdtemp())
        temp_video_file = temp_dir / "video.mkv"
        temp_audio_file = temp_dir / "audio.flac"

        video_writer_transform = VideoWriterTransform(temp_video_file)
        audio_writer_transform = AudioWriterTransform(temp_audio_file)
        video_audio_muxer_sink = VideoAudioMuxerSink(Path(self._config.video_file))

        visualizer_sink = VisualizerSink(session_context.widget_service, "Video Preview")

        shared_video_source = Stream(video_source.descriptor, video_source.observable.pipe(ops.observe_on(self._main_scheduler), ops.share()))

        video_writer_stream = Stream(shared_video_source.descriptor, shared_video_source.observable.pipe(ops.observe_on(self._writer_scheduler)))
        audio_writer_stream = Stream(audio_source.descriptor, audio_source.observable.pipe(ops.observe_on(self._writer_scheduler)))

        video_file_stream = video_writer_transform.pipe(video_writer_stream)
        audio_file_stream = audio_writer_transform.pipe(audio_writer_stream)

        video_audio_muxer_stream = Stream(
            rx.combine_latest(video_file_stream.descriptor, audio_file_stream.descriptor),
            rx.zip(video_file_stream.observable, audio_file_stream.observable)
        )
        muxer_sub = video_audio_muxer_sink.subscribe(video_audio_muxer_stream)

        visualizer_sub = visualizer_sink.subscribe(shared_video_source)

        disposable = CompositeDisposable(muxer_sub, visualizer_sub)
        primary_done = muxer_sub.done

        return PipelineSubscription(disposable, primary_done)

    def dispose(self):
        if self._widget_handle:
            self._widget_handle.dispose()
