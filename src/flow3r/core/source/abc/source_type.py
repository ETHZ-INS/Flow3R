from dataclasses import dataclass
from typing import Protocol, TypeVar, Callable, Tuple, Generic

from PySide6.QtWidgets import QWidget

from flow3r.core.source.abc.source_config import ISourceConfig
from flow3r.core.source.abc.source import ISource
from flow3r.core.widgets.config_widget import IConfigWidget

TConfig = TypeVar("TConfig", bound=ISourceConfig)
TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class ISourceType(Protocol[TConfig, TDesc, TData]):
    """Protocol that describes a *kind* of source (e.g. "Webcam", "Pylon Camera").

    Flow3R uses :class:`ISourceType` objects as factories.  When a user adds a
    source in the UI, the application calls the relevant factory callables to
    create a default config, a config-editing widget, and ultimately a live
    source instance.

    Use the concrete :class:`SourceType` dataclass when registering a source type
    from a plugin — it satisfies this protocol automatically.
    """

    @property
    def name(self) -> str:
        """Unique, human-readable name shown in the *Add Source* dialog (e.g. ``"Webcam"``)."""
        ...

    @property
    def category(self) -> Tuple[str, ...]:
        """Hierarchical category path used to group sources in menus (e.g. ``("Video", "Camera")``)."""
        ...

    @property
    def config_factory(self) -> Callable[[], TConfig]:
        """Zero-argument callable that returns a default source config instance."""
        ...

    @property
    def config_widget_factory(self) -> Callable[[TConfig, QWidget], IConfigWidget]:
        """Callable ``(config, parent) -> IConfigWidget`` that creates the source config editor widget."""
        ...

    @property
    def source_factory(self) -> Callable[[TConfig], ISource[TDesc, TData]]:
        """Callable ``(config) -> ISource`` that constructs a live source instance."""
        ...


@dataclass
class SourceType(Generic[TConfig, TDesc, TData]):
    """Concrete dataclass implementation of :class:`ISourceType`.

    Create one of these and pass it to
    :meth:`~flow3r.app.api.plugins.source_type_registry.SourceTypeRegistry.register`
    inside your plugin's :meth:`~flow3r.core.plugin.plugin.IPlugin.initialize` method.

    Example::

        MY_SOURCE_TYPE = SourceType(
            name="My Camera",
            category=("Video", "Camera"),
            config_factory=MyCameraConfig,
            config_widget_factory=MyCameraConfigWidget,
            source_factory=MyCameraSource,
        )

        # inside IPlugin.initialize:
        api.source_types.register(MY_SOURCE_TYPE)
    """

    name: str
    """Unique, human-readable name shown in the *Add Source* dialog."""

    category: Tuple[str, ...]
    """Hierarchical category path (e.g. ``("Video", "Camera")``)."""

    config_factory: Callable[[], TConfig]
    """Zero-argument callable that returns a default source config instance."""

    config_widget_factory: Callable[[TConfig, QWidget], IConfigWidget]
    """Callable ``(config, parent) -> IConfigWidget`` for the config editor widget."""

    source_factory: Callable[[TConfig], ISource[TDesc, TData]]
    """Callable ``(config) -> ISource`` that constructs a live source instance."""
