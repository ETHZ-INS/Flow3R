from typing import Callable

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.source.abc.source_type import ISourceType
from aaaflow3r.plugins.core.source.audio.audio_file.config import AudioFileSourceConfig
from aaaflow3r.plugins.core.source.audio.audio_file.config_widget import AudioFileSourceConfigWidget
from aaaflow3r.plugins.core.source.audio.audio_file.source import AudioFileSource
from aaaflow3r.plugins.core.typing.audio import AudioFormat, AudioChunk


class AudioFileSourceType(ISourceType[AudioFileSourceConfig, AudioFormat, AudioChunk]):
    @property
    def name(self) -> str:
        return "Audio File"

    @property
    def category(self) -> str:
        return "Audio"

    @property
    def visualizer_type(self) -> str:
        return "Audio"
    
    @property
    def live(self) -> bool:
        return True

    def get_config_factory(self) -> Callable[[], AudioFileSourceConfig]:
        return AudioFileSourceConfig

    def get_config_widget_factory(self) -> Callable[[AudioFileSourceConfig, QWidget], QWidget]:
        return AudioFileSourceConfigWidget

    def get_source_factory(self) -> Callable[[AudioFileSourceConfig], AudioFileSource]:
        return AudioFileSource
