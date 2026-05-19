from typing import Protocol

from flow3r.app.api.plugins.visualizer_type_registry import VisualizerTypeRegistry
from flow3r.core.api.plugins.config_type_registry import IConfigTypeRegistry
from flow3r.core.api.plugins.pipeline_type_registry import IPipelineTypeRegistry
from flow3r.core.api.plugins.settings_menus_registry import ISettingsMenusRegistry
from flow3r.core.api.plugins.settings_registry import ISettingsRegistry
from flow3r.core.api.plugins.source_type_registry import ISourceTypeRegistry


class IPluginAPI(Protocol):
    @property
    def config_types(self) -> IConfigTypeRegistry: ...
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
