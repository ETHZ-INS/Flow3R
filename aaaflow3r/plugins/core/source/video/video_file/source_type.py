from typing import Callable, Tuple

import numpy as np
from PySide6.QtWidgets import QWidget
from py3r.media.types import VideoFrame

from aaaflow3r.core.source.abc.source_type import ISourceType
from aaaflow3r.plugins.core.source.video.video_file.config import VideoFileSourceConfig
from aaaflow3r.plugins.core.source.video.video_file.config_widget import VideoFileSourceConfigWidget
from aaaflow3r.plugins.core.source.video.video_file.source import VideoFileSource
from aaaflow3r.plugins.core.typing.video import VideoFormat


class VideoFileSourceType(ISourceType[VideoFileSourceConfig, VideoFormat, VideoFrame]):
    @property
    def name(self) -> str:
        return "Video File"

    @property
    def category(self) -> Tuple[str, ...]:
        return ("Video",)

    @property
    def visualizer_type(self) -> str:
        return "Video"

    @property
    def live(self) -> bool:
        return False

    def get_config_factory(self) -> Callable[[], VideoFileSourceConfig]:
        return VideoFileSourceConfig

    def get_config_widget_factory(self) -> Callable[[VideoFileSourceConfig, QWidget], QWidget]:
        return VideoFileSourceConfigWidget

    def get_source_factory(self) -> Callable[[VideoFileSourceConfig], VideoFileSource]:
        return VideoFileSource
