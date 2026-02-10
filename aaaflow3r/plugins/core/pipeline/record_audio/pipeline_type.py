from typing import Callable

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.pipeline.abc.pipeline_type import IPipelineType
from aaaflow3r.plugins.core.pipeline.record_audio.config import RecordAudioConfig
from aaaflow3r.plugins.core.pipeline.record_audio.config_widget import RecordAudioConfigWidget
from aaaflow3r.plugins.core.pipeline.record_audio.pipeline import RecordAudioPipeline


class RecordAudioPipelineType(IPipelineType[RecordAudioConfig, RecordAudioPipeline]):
    @property
    def name(self) -> str:
        return "Record Audio"

    def get_config_factory(self) -> Callable[[], RecordAudioConfig]:
        return RecordAudioConfig

    def get_config_widget_factory(self) -> Callable[[RecordAudioConfig, QWidget], QWidget]:
        return RecordAudioConfigWidget

    def get_pipeline_factory(self) -> Callable[[], RecordAudioPipeline]:
        return RecordAudioPipeline
