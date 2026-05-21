from pathlib import Path
from typing import Optional, Dict

import reactivex as rx
from reactivex import operators as ops
from flow3r.core.pipeline.abc.pipeline import ConfigureContext, PreviewContext, PipelineContext, PipelineBase
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.pipeline.record_audio.config import RecordAudioConfig
from flow3r.plugins.core.node.audio_writer import AudioWriterSink


class RecordAudioPipeline(PipelineBase[RecordAudioConfig]):
    def __init__(self):
        self._config: Optional[RecordAudioConfig] = None

    def configure(self, context: ConfigureContext[RecordAudioConfig]) -> None:
        self._config = context.config

    def preview(self, context: PreviewContext[RecordAudioConfig], sources: Dict[str, IStream]) -> None:
        context.register_done(rx.from_list([None]))

    def build(self, context: PipelineContext[RecordAudioConfig], sources: Dict[str, IStream]) -> None:
        source = sources["Audio"]

        audio_writer_sink = AudioWriterSink(Path(context.config.audio_file))

        shared_source = Stream(source.format, source.data.pipe(ops.share()))
        audio_writer_sub = audio_writer_sink.subscribe(shared_source)

        context.register_primary_done(audio_writer_sub.done)
        context.add_disposable(audio_writer_sub.disposable)

    def dispose(self):
        pass
