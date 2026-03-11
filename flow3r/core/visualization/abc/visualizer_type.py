from typing import Protocol, Any, Callable

from PySide6.QtWidgets import QWidget


class IVisualizer(Protocol):
    def visualize(self, data: dict): ...


class IVisualizerType(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def widget_factory(self) -> Callable[[QWidget], QWidget]: ...
    def accepts(self, desc: Any) -> bool: ...
