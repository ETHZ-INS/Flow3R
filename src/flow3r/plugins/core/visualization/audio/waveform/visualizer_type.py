from typing import Any

from flow3r.core.visualization.abc.visualizer_type import IVisualizerType
from flow3r.core.visualization.visualizer_handle import VisualizerHandle
from flow3r.plugins.core.typing.audio import AudioFormat
from flow3r.plugins.core.visualization.audio.waveform.widget import WaveformWidget


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

    def accepts(self, fmt: Any) -> bool:
        return isinstance(fmt, AudioFormat)
