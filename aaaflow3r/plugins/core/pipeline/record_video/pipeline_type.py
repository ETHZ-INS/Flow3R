from typing import Callable

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.pipeline.abc.pipeline_type import IPipelineType
from aaaflow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig
from aaaflow3r.plugins.core.pipeline.record_video.config_widget import RecordVideoConfigWidget
from aaaflow3r.plugins.core.pipeline.record_video.pipeline import RecordVideoPipeline


class RecordVideoPipelineType(IPipelineType[RecordVideoConfig, RecordVideoPipeline]):
    @property
    def name(self) -> str:
        return "Record Video"

    def get_config_factory(self) -> Callable[[], RecordVideoConfig]:
        return RecordVideoConfig

    def get_config_widget_factory(self) -> Callable[[RecordVideoConfig, QWidget], QWidget]:
        return RecordVideoConfigWidget

    def get_pipeline_factory(self) -> Callable[[], RecordVideoPipeline]:
        return RecordVideoPipeline
