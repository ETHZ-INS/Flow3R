from typing import Protocol

from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


class IWidgetService(Protocol):
    def get_visualizer_handle(self, widget_type_name: str, widget_id: str, session_id: str) -> IVisualizerHandle: ...
