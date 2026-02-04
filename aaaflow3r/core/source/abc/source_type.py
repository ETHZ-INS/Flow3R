from typing import Protocol, TypeVar, Callable

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.source.abc.source import ISource

TConfig = TypeVar("TConfig")  # TODO: bound to config type interface
TDesc = TypeVar("TDesc")
TData = TypeVar("TData")


class ISourceType(Protocol[TConfig, TDesc, TData]):
    @property
    def name(self) -> str: ...
    @property
    def category(self) -> str: ...
    @property
    def visualizer_type(self) -> str: ...
    @property
    def live(self) -> bool: ...
    def get_config_factory(self) -> Callable[[], TConfig]: ...
    def get_config_widget_factory(self) -> Callable[[TConfig, QWidget], QWidget]: ...
    def get_source_factory(self) -> Callable[[TConfig], ISource[TDesc, TData]]: ...  # TODO: Think about whether one source/device can have multiple streams
