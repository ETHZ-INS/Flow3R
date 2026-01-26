from typing import Protocol

from aaaflow3r.app.api.plugins.visualizer_type_registry import VisualizerTypeRegistry
from aaaflow3r.core.api.plugins.pipeline_type_registry import IPipelineTypeRegistry
from aaaflow3r.core.api.plugins.source_type_registry import ISourceTypeRegistry


class IPluginAPI(Protocol):
    @property
    def source_types(self) -> ISourceTypeRegistry: ...
    @property
    def visualizer_types(self) -> VisualizerTypeRegistry: ...
    @property
    def pipeline_types(self) -> IPipelineTypeRegistry: ...
