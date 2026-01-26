from typing import Callable

import numpy as np
from PySide6.QtWidgets import QWidget

from aaaflow3r.core.source.abc.source_type import ISourceType, Stream
from aaaflow3r.plugins.core.source.video.video_file.config import VideoFileSourceConfig
from aaaflow3r.plugins.core.source.video.video_file.config_widget import VideoFileSourceConfigWidget


class VideoFileSourceType(ISourceType[VideoFileSourceConfig, np.ndarray]):
    @property
    def name(self) -> str:
        return "Video File"

    @property
    def category(self) -> str:
        return "Video"

    @property
    def live(self) -> bool:
        return False

    def get_config_factory(self) -> Callable[[], VideoFileSourceConfig]:
        return VideoFileSourceConfig

    def get_config_widget_factory(self) -> Callable[[VideoFileSourceConfig, QWidget], QWidget]:
        return VideoFileSourceConfigWidget

    def get_source_factory(self) -> Callable[[VideoFileSourceConfig], Stream[np.ndarray]]:
        ...
