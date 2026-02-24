from typing import Callable, Tuple

import numpy as np
from PySide6.QtWidgets import QWidget
from py3r.media.types import VideoFrame

from flow3r.core.source.abc.source_type import ISourceType
from flow3r.plugins.core.source.video.pylon.config import PylonCameraSourceConfig
from flow3r.plugins.core.source.video.pylon.config_widget import PylonCameraSourceConfigWidget
from flow3r.plugins.core.source.video.pylon.source import PylonCameraSource
from flow3r.plugins.core.typing.video import VideoFormat


class PylonCameraSourceType(ISourceType[PylonCameraSourceConfig, VideoFormat, VideoFrame]):
    @property
    def name(self) -> str:
        return "Pylon Camera"

    @property
    def category(self) -> Tuple[str, ...]:
        return ("Video",)

    @property
    def visualizer_type(self) -> str:
        return "Video"

    @property
    def live(self) -> bool:
        return False

    def get_config_factory(self) -> Callable[[], PylonCameraSourceConfig]:
        return PylonCameraSourceConfig

    def get_config_widget_factory(self) -> Callable[[PylonCameraSourceConfig, QWidget], QWidget]:
        return PylonCameraSourceConfigWidget

    def get_source_factory(self) -> Callable[[PylonCameraSourceConfig], PylonCameraSource]:
        return PylonCameraSource
