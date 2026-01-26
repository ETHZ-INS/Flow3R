from typing import Callable

from PySide6.QtWidgets import QWidget
from py3r.media.types import VideoFrame

from aaaflow3r.core.source.abc.source_type import ISourceType
from aaaflow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig
from aaaflow3r.plugins.core.source.video.webcam.config_widget import WebcamSourceConfigWidget
from aaaflow3r.plugins.core.source.video.webcam.source import WebcamSource


class WebcamSourceType(ISourceType[WebcamSourceConfig, VideoFrame]):
    @property
    def name(self) -> str:
        return "Webcam"

    @property
    def category(self) -> str:
        return "Video"

    @property
    def visualizer_type(self) -> str:
        return "Video"

    @property
    def live(self) -> bool:
        return True

    def get_config_factory(self) -> Callable[[], WebcamSourceConfig]:
        return WebcamSourceConfig

    def get_config_widget_factory(self) -> Callable[[WebcamSourceConfig, QWidget], QWidget]:
        return WebcamSourceConfigWidget

    def get_source_factory(self) -> Callable[[WebcamSourceConfig], WebcamSource]:
        return WebcamSource
