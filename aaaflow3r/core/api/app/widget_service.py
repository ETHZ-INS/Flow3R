from typing import Protocol

from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


class IWidgetService(Protocol):
    def get_visualizer_handle(self, widget_id: str) -> IVisualizerHandle: ...
