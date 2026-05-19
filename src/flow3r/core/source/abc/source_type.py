from dataclasses import dataclass
from typing import Protocol, TypeVar, Callable, Tuple, Generic

from PySide6.QtWidgets import QWidget

from flow3r.core.source.abc.source_config import ISourceConfig
from flow3r.core.source.abc.source import ISource
from flow3r.core.widgets.config_widget import IConfigWidget

TConfig = TypeVar("TConfig", bound=ISourceConfig)  # TODO: bound to config type interface
TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class ISourceType(Protocol[TConfig, TDesc, TData]):
    @property
    def name(self) -> str: ...
    @property
    def category(self) -> Tuple[str, ...]: ...
    @property
    def config_factory(self) -> Callable[[], TConfig]: ...
    @property
    def config_widget_factory(self) -> Callable[[TConfig, QWidget], IConfigWidget]: ...
    @property
    def source_factory(self) -> Callable[[TConfig], ISource[TDesc, TData]]: ...  # TODO: Think about whether one source/device can have multiple streams


@dataclass
class SourceType(Generic[TConfig, TDesc, TData]):
    name: str
    category: Tuple[str, ...]
    config_factory: Callable[[], TConfig]
    config_widget_factory: Callable[[TConfig, QWidget], IConfigWidget]
    source_factory: Callable[[TConfig], ISource[TDesc, TData]]
