from aaaflow3r.app.api.plugins.pipeline_type_registry import PipelineTypeRegistry
from aaaflow3r.app.api.plugins.source_type_registry import SourceTypeRegistry
from aaaflow3r.app.api.plugins.visualizer_type_registry import VisualizerTypeRegistry
from aaaflow3r.core.api.plugins.plugins import IPluginAPI


class PluginAPI(IPluginAPI):
    def __init__(self):
        self._source_types = SourceTypeRegistry()
        self._visualizer_types = VisualizerTypeRegistry()
        self._pipeline_types = PipelineTypeRegistry()

    @property
    def source_types(self) -> SourceTypeRegistry:
        return self._source_types

    @property
    def visualizer_types(self) -> VisualizerTypeRegistry:
        return self._visualizer_types

    @property
    def pipeline_types(self) -> PipelineTypeRegistry:
        return self._pipeline_types
