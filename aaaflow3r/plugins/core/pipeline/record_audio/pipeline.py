from pathlib import Path
from typing import List, Optional

import reactivex as rx
from reactivex import operators as ops
from reactivex.disposable import CompositeDisposable

from aaaflow3r.core.api.app.session_context import ISessionContext
from aaaflow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription
from aaaflow3r.core.streaming.abc.stream import IStream
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.core.visualization.visualizer_sink import VisualizerSink
from aaaflow3r.plugins.core.pipeline.record_audio.config import RecordAudioConfig
from aaaflow3r.plugins.core.node.audio_writer import AudioWriterSink


class RecordAudioPipeline(IPipeline[RecordAudioConfig]):
    def __init__(self):
        self._widget_handle: Optional[IVisualizerHandle] = None
        self._config: Optional[RecordAudioConfig] = None

    def configure(self, session_context: ISessionContext, config: RecordAudioConfig):
        self._config = config
        if not self._widget_handle:
            self._widget_handle = session_context.widget_service.get_visualizer_handle("my_audio")

    def build(self, session_context: ISessionContext, sources: List[IStream]) -> PipelineSubscription:
        assert len(sources) == 1
        source = sources[0]

        audio_writer_sink = AudioWriterSink(Path(self._config.audio_file))
        visualizer_sink = VisualizerSink(session_context.widget_service, "my_audio")

        shared_source = Stream(source.descriptor, source.observable.pipe(ops.share()))
        audio_writer_sub = audio_writer_sink.subscribe(shared_source)
        visualizer_sub = visualizer_sink.subscribe(shared_source)

        disposable = CompositeDisposable(audio_writer_sub, visualizer_sub)
        primary_done = rx.zip(audio_writer_sub.done, visualizer_sub.done)
        return PipelineSubscription(disposable, primary_done)

    def dispose(self):
        if self._widget_handle:
            self._widget_handle.dispose()
