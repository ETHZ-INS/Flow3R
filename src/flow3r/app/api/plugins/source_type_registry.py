from typing import Dict

from flow3r.core.api.plugins.source_type_registry import ISourceTypeRegistry
from flow3r.core.source.abc.source_type import ISourceType


class SourceTypeRegistry(ISourceTypeRegistry):
    """Concrete registry that maps source type names to :class:`ISourceType` objects.

    Plugins call :meth:`register` inside :meth:`~flow3r.core.plugin.plugin.IPlugin.initialize`
    to make their source types available in the *Add Source* dialog.
    """

    def __init__(self):
        self._source_types = {}

    def register(self, source_type: ISourceType) -> None:
        """Register a source type with the application.

        Args:
            source_type: A fully configured :class:`~flow3r.core.source.abc.source_type.SourceType`
                (or any object satisfying :class:`~flow3r.core.source.abc.source_type.ISourceType`)
                describing how to create config objects, config widgets, and source instances.
        """
        self._source_types[source_type.name] = source_type

    def get_source_types(self) -> Dict[str, ISourceType]:
        """Return all registered source types keyed by name."""
        return self._source_types
