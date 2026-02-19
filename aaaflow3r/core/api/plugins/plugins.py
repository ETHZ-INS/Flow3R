from typing import Protocol

from aaaflow3r.app.api.plugins.visualizer_type_registry import VisualizerTypeRegistry
from aaaflow3r.core.api.plugins.pipeline_type_registry import IPipelineTypeRegistry
from aaaflow3r.core.api.plugins.settings_menus_registry import ISettingsMenusRegistry
from aaaflow3r.core.api.plugins.settings_registry import ISettingsRegistry
from aaaflow3r.core.api.plugins.source_type_registry import ISourceTypeRegistry


class IPluginAPI(Protocol):
    @property
    def source_types(self) -> ISourceTypeRegistry: ...
    @property
    def visualizer_types(self) -> VisualizerTypeRegistry: ...
    @property
    def pipeline_types(self) -> IPipelineTypeRegistry: ...
    @property
    def settings(self) -> ISettingsRegistry: ...
    @property
    def settings_menus(self) -> ISettingsMenusRegistry: ...
