from typing import Callable

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.pipeline.abc.pipeline_type import IPipelineType
from aaaflow3r.plugins.core.pipeline.record_video_with_audio.config import RecordVideoWithAudioConfig
from aaaflow3r.plugins.core.pipeline.record_video_with_audio.config_widget import RecordVideoWithAudioConfigWidget
from aaaflow3r.plugins.core.pipeline.record_video_with_audio.pipeline import RecordVideoWithAudioPipeline


class RecordVideoWithAudioPipelineType(IPipelineType[RecordVideoWithAudioConfig, RecordVideoWithAudioPipeline]):
    @property
    def name(self) -> str:
        return "Record Video with Audio"

    def get_config_factory(self) -> Callable[[], RecordVideoWithAudioConfig]:
        return RecordVideoWithAudioConfig

    def get_config_widget_factory(self) -> Callable[[IAppContext, RecordVideoWithAudioConfig, QWidget], QWidget]:
        return RecordVideoWithAudioConfigWidget

    def get_pipeline_factory(self) -> Callable[[], RecordVideoWithAudioPipeline]:
        return RecordVideoWithAudioPipeline
