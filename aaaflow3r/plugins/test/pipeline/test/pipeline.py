from typing import List, Any

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.pipeline.abc.pipeline import IPipeline
from aaaflow3r.core.streaming.abc.stream import IStream
from aaaflow3r.plugins.core.typing.video import VideoFormat


class TestPipeline(IPipeline):
    def __init__(self):
        self.leases = []

    def build(self, app_context: IAppContext, sources: List[IStream]) -> Any:
        def build_widget(source: IStream, desc: Any, widget_id: str):
            if isinstance(desc, VideoFormat):
                widget_handle_lease = app_context.widget_service.get_visualizer_handle("Video", widget_id, "abc")
                widget_handle_lease.handle.subscribe(source)
                self.leases.append(widget_handle_lease)
            else:
                widget_handle_lease = app_context.widget_service.get_visualizer_handle("Audio", widget_id, "abc")
                widget_handle_lease.handle.subscribe(source)
                self.leases.append(widget_handle_lease)

        for i, source in enumerate(sources):
            source.descriptor.subscribe(on_next=lambda desc, src=source, wi=i: build_widget(src, desc, f"source_{wi}"))
