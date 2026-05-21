from typing import Protocol

from flow3r.app.api.plugins.visualizer_type_registry import VisualizerTypeRegistry
from flow3r.core.api.plugins.config_type_registry import IConfigTypeRegistry
from flow3r.core.api.plugins.pipeline_type_registry import IPipelineTypeRegistry
from flow3r.core.api.plugins.settings_menus_registry import ISettingsMenusRegistry
from flow3r.core.api.plugins.settings_registry import ISettingsRegistry
from flow3r.core.api.plugins.source_type_registry import ISourceTypeRegistry


class IPluginAPI(Protocol):
    """Read-only protocol describing the API surface available to plugins.

    An instance of this protocol is passed to :meth:`IPlugin.initialize` for
    every loaded plugin.  Plugins use the registry properties to register their
    contributions (source types, pipeline types, etc.) with the application.

    The concrete implementation is :class:`flow3r.app.api.plugins.plugins.PluginAPI`.
    """

    @property
    def config_types(self) -> IConfigTypeRegistry:
        """Registry for mapping ``TYPE_ID`` strings to config dataclasses.

        Plugins must register a config class here for every source config and
        pipeline config they introduce so that Flow3R can deserialise saved
        ``.f3r`` project files correctly.
        """
        ...

    @property
    def source_types(self) -> ISourceTypeRegistry:
        """Registry for :class:`~flow3r.core.source.abc.source_type.ISourceType` objects.

        Each registered source type appears in the *Add Source* dialog and can
        be instantiated by the user when building a recording project.
        """
        ...

    @property
    def visualizer_types(self) -> VisualizerTypeRegistry:
        """Registry for visualizer types (live preview widgets)."""
        ...

    @property
    def pipeline_types(self) -> IPipelineTypeRegistry:
        """Registry for :class:`~flow3r.core.pipeline.abc.pipeline_type.IPipelineType` objects.

        Each registered pipeline type appears in the *Add Pipeline* dialog and
        can be attached to a recording group.
        """
        ...

    @property
    def settings(self) -> ISettingsRegistry:
        """Registry for application-wide settings keys and their default values."""
        ...

    @property
    def settings_menus(self) -> ISettingsMenusRegistry:
        """Registry for plugin-contributed entries in the Settings menu."""
        ...
