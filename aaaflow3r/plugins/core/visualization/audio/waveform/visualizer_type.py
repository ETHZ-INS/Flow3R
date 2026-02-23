from typing import Any

from aaaflow3r.core.visualization.abc.visualizer_type import IVisualizerType
from aaaflow3r.core.visualization.visualizer_handle import VisualizerHandle
from aaaflow3r.plugins.core.typing.audio import AudioFormat
from aaaflow3r.plugins.core.visualization.audio.waveform.widget import WaveformWidget


class WaveformVisualizerType(IVisualizerType):
    @property
    def name(self) -> str:
        return "Waveform"

    @property
    def handle_factory(self):
        return VisualizerHandle

    @property
    def widget_factory(self):
        return WaveformWidget

    def accepts(self, desc: Any) -> bool:
        return isinstance(desc, AudioFormat)
