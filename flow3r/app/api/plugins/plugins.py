from flow3r.app.api.plugins.pipeline_type_registry import PipelineTypeRegistry
from flow3r.app.api.plugins.settings_menu_registry import SettingsMenuRegistry
from flow3r.app.api.plugins.settings_registry import SettingsRegistry
from flow3r.app.api.plugins.source_type_registry import SourceTypeRegistry
from flow3r.app.api.plugins.visualizer_type_registry import VisualizerTypeRegistry
from flow3r.core.api.plugins.plugins import IPluginAPI


class PluginAPI(IPluginAPI):
    def __init__(self):
        self._source_types = SourceTypeRegistry()
        self._visualizer_types = VisualizerTypeRegistry()
        self._pipeline_types = PipelineTypeRegistry()
        self._settings_registry = SettingsRegistry()
        self._settings_menus = SettingsMenuRegistry()

    @property
    def source_types(self) -> SourceTypeRegistry:
        return self._source_types

    @property
    def visualizer_types(self) -> VisualizerTypeRegistry:
        return self._visualizer_types

    @property
    def pipeline_types(self) -> PipelineTypeRegistry:
        return self._pipeline_types

    @property
    def settings(self) -> SettingsRegistry:
        return self._settings_registry

    @property
    def settings_menus(self) -> SettingsMenuRegistry:
        return self._settings_menus
