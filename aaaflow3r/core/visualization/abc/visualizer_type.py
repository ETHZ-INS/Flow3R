from typing import Protocol, List, Type


class IVisualizer(Protocol):
    def visualize(self, data: dict): ...


class IVisualizerType(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def handle_factory(self): ...
    @property
    def widget_factory(self): ...
