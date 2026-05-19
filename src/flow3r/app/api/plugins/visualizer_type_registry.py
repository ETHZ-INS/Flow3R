from typing import Dict

from flow3r.core.api.plugins.visualizer_type_registry import IVisualizerRegistry
from flow3r.core.visualization.abc.visualizer_type import IVisualizerType


class VisualizerTypeRegistry(IVisualizerRegistry):
    def __init__(self):
        self._visualizer_types = {}

    def register(self, source_type: IVisualizerType):
        self._visualizer_types[source_type.name] = source_type

    def get_visualizer_types(self) -> Dict[str, IVisualizerType]:
        return self._visualizer_types
