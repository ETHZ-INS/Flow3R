from typing import Protocol, Any, Callable

from PySide6.QtWidgets import QWidget


class IVisualizerType(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def widget_factory(self) -> Callable[[QWidget], QWidget]: ...
    def accepts(self, fmt: Any) -> bool: ...
