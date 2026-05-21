from typing import Dict

from flow3r.core.api.plugins.pipeline_type_registry import IPipelineTypeRegistry
from flow3r.core.pipeline.abc.pipeline_type import IPipelineType


class PipelineTypeRegistry(IPipelineTypeRegistry):
    """Concrete registry that maps pipeline type names to :class:`IPipelineType` objects.

    Plugins call :meth:`register` inside :meth:`~flow3r.core.plugin.plugin.IPlugin.initialize`
    to make their pipeline types available in the *Add Pipeline* dialog.
    """

    def __init__(self):
        self._pipeline_types = {}

    def register(self, pipeline_type: IPipelineType) -> None:
        """Register a pipeline type with the application.

        Args:
            pipeline_type: A fully configured :class:`~flow3r.core.pipeline.abc.pipeline_type.PipelineType`
                (or any object satisfying :class:`~flow3r.core.pipeline.abc.pipeline_type.IPipelineType`)
                describing how to create config objects, config widgets, and pipeline instances.
        """
        self._pipeline_types[pipeline_type.name] = pipeline_type

    def get_pipeline_types(self) -> Dict[str, IPipelineType]:
        """Return all registered pipeline types keyed by name."""
        return self._pipeline_types
