from typing import Protocol, runtime_checkable

from flow3r.core.api.plugins.plugins import IPluginAPI


@runtime_checkable
class IPlugin(Protocol):
    """Interface that every Flow3R plugin must satisfy.

    A plugin is the single entry-point object that Flow3R instantiates when it
    discovers a ``flow3r.plugins`` entry-point group.  Its only responsibility
    is to call the relevant ``api.*.register(...)`` methods during
    :meth:`initialize` so that the application becomes aware of the source
    types, pipeline types, visualizers, and settings the plugin provides.

    Example package entry-point declaration (``pyproject.toml``)::

        [project.entry-points."flow3r.plugins"]
        my_plugin = "my_package.plugin:MyPlugin"
    """

    @property
    def name(self) -> str:
        """Human-readable name of the plugin (used in log messages)."""
        ...

    def initialize(self, api: IPluginAPI) -> None:
        """Register all plugin contributions with the application.

        Called exactly once, before the main window is shown.  Use *api* to
        register source types, pipeline types, visualizers, config types, and
        settings menus.

        Args:
            api: The plugin API surface provided by the application.
        """
        ...
