from typing import Callable

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.source.abc.source_type import ISourceType
from aaaflow3r.plugins.core.source.audio.microphone.config import MicrophoneSourceConfig
from aaaflow3r.plugins.core.source.audio.microphone.config_widget import MicrophoneSourceConfigWidget
from aaaflow3r.plugins.core.source.audio.microphone.source import MicrophoneSource
from aaaflow3r.plugins.core.typing.audio import AudioFormat, AudioChunk


class MicrophoneSourceType(ISourceType[MicrophoneSourceConfig, AudioFormat, AudioChunk]):
    @property
    def name(self) -> str:
        return "Microphone"

    @property
    def category(self) -> str:
        return "Audio"

    @property
    def visualizer_type(self) -> str:
        return "Audio"
    
    @property
    def live(self) -> bool:
        return True

    def get_config_factory(self) -> Callable[[], MicrophoneSourceConfig]:
        return MicrophoneSourceConfig

    def get_config_widget_factory(self) -> Callable[[MicrophoneSourceConfig, QWidget], QWidget]:
        return MicrophoneSourceConfigWidget

    def get_source_factory(self) -> Callable[[MicrophoneSourceConfig], MicrophoneSource]:
        return MicrophoneSource
