from dataclasses import dataclass
from typing import Protocol, TypeVar, Callable, Any, Generic

from PySide6.QtWidgets import QWidget
from reactivex.observable import Observable

from aaaflow3r.core.source.abc.source import ISource

TConfig = TypeVar("TConfig")  # TODO: bound to config type interface
TStream = TypeVar("TStream")


class ISourceType(Protocol[TConfig, TStream]):
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
    def get_source_factory(self) -> Callable[[TConfig], ISource]: ...  # TODO: Think about whether one source/device can have multiple streams
