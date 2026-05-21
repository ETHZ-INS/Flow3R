from dataclasses import dataclass
from typing import Protocol, Callable, TypeVar, Tuple, Generic

from PySide6.QtWidgets import QWidget

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.pipeline.abc.pipeline import IPipeline
from flow3r.core.widgets.config_widget import IConfigWidget

TConfig = TypeVar("TConfig")
TPipeline = TypeVar("TPipeline", bound=IPipeline)


class IPipelineType(Protocol[TConfig, TPipeline]):
    """Protocol that describes a *kind* of pipeline (e.g. "Record Video").

    Flow3R uses :class:`IPipelineType` objects as factories.  When a user adds a
    pipeline to a group, the application calls the factory callables to create a
    default config, a config-editing widget, and ultimately a pipeline instance.

    Use the concrete :class:`PipelineType` dataclass when registering a pipeline
    type from a plugin — it satisfies this protocol automatically.
    """

    @property
    def name(self) -> str:
        """Unique, human-readable name shown in the *Add Pipeline* dialog (e.g. ``"Record Video"``)."""
        ...

    @property
    def category(self) -> Tuple[str, ...]:
        """Hierarchical category path used to group pipelines in menus (e.g. ``("Video",)``)."""
        ...

    @property
    def config_factory(self) -> Callable[[], TConfig]:
        """Zero-argument callable that returns a default pipeline config instance."""
        ...

    @property
    def config_widget_factory(self) -> Callable[[IAppContext, TConfig, QWidget], IConfigWidget]:
        """Callable ``(app_context, config, parent) -> IConfigWidget`` for the config editor widget."""
        ...

    @property
    def pipeline_factory(self) -> Callable[[], IPipeline]:
        """Zero-argument callable that constructs a new pipeline instance."""
        ...


@dataclass
class PipelineType(Generic[TConfig, TPipeline]):
    """Concrete dataclass implementation of :class:`IPipelineType`.

    Create one of these and pass it to
    :meth:`~flow3r.app.api.plugins.pipeline_type_registry.PipelineTypeRegistry.register`
    inside your plugin's :meth:`~flow3r.core.plugin.plugin.IPlugin.initialize` method.

    Example::

        MY_PIPELINE_TYPE = PipelineType(
            name="My Analysis",
            category=("Analysis",),
            config_factory=MyAnalysisConfig,
            config_widget_factory=MyAnalysisConfigWidget,
            pipeline_factory=MyAnalysisPipeline,
        )

        # inside IPlugin.initialize:
        api.pipeline_types.register(MY_PIPELINE_TYPE)
    """

    name: str
    """Unique, human-readable name shown in the *Add Pipeline* dialog."""

    category: Tuple[str, ...]
    """Hierarchical category path (e.g. ``("Video",)``)."""

    config_factory: Callable[[], TConfig]
    """Zero-argument callable that returns a default pipeline config instance."""

    config_widget_factory: Callable[[IAppContext, TConfig, QWidget], IConfigWidget]
    """Callable ``(app_context, config, parent) -> IConfigWidget`` for the config editor widget."""

    pipeline_factory: Callable[[], IPipeline]
    """Zero-argument callable that constructs a new pipeline instance."""
