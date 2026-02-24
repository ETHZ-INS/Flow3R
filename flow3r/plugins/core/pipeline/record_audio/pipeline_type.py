from typing import Callable

from PySide6.QtWidgets import QWidget

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.pipeline.abc.pipeline_type import IPipelineType
from flow3r.plugins.core.pipeline.record_audio.config import RecordAudioConfig
from flow3r.plugins.core.pipeline.record_audio.config_widget import RecordAudioConfigWidget
from flow3r.plugins.core.pipeline.record_audio.pipeline import RecordAudioPipeline


class RecordAudioPipelineType(IPipelineType[RecordAudioConfig, RecordAudioPipeline]):
    @property
    def name(self) -> str:
        return "Record Audio"

    def get_config_factory(self) -> Callable[[], RecordAudioConfig]:
        return RecordAudioConfig

    def get_config_widget_factory(self) -> Callable[[IAppContext, RecordAudioConfig, QWidget], QWidget]:
        return RecordAudioConfigWidget

    def get_pipeline_factory(self) -> Callable[[], RecordAudioPipeline]:
        return RecordAudioPipeline
