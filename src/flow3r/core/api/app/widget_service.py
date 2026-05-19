from typing import Protocol

from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


class IWidgetService(Protocol):
    def get_visualizer_handle(self, widget_id: str) -> IVisualizerHandle: ...
