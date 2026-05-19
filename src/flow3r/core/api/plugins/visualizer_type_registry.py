from typing import Protocol

from flow3r.core.visualization.abc.visualizer_type import IVisualizerType


class IVisualizerRegistry(Protocol):
    def register(self, visualizer_type: IVisualizerType): ...
