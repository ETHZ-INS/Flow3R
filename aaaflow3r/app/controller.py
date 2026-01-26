import uuid
from copy import deepcopy
from typing import Dict

from PySide6.QtCore import QObject, Signal
from reactivex import Subject
from reactivex.scheduler import EventLoopScheduler
from reactivex.subject import ReplaySubject

from aaaflow3r.app.api.app.app_context import AppContext
from aaaflow3r.app.config.app_config import AppConfig
from aaaflow3r.app.widget_service import WidgetService
from aaaflow3r.core.pipeline.abc.pipeline_type import IPipelineType
from aaaflow3r.core.pipeline.pipeline_config import PipelineConfig
from aaaflow3r.core.source.abc.source import ISource
from aaaflow3r.core.source.abc.source_type import ISourceType
from aaaflow3r.core.source.source_config import SourceConfig
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


class ErrorSource(ISource):
    def __init__(self, exc: Exception):
        self._exc = exc
        self._descriptor = ReplaySubject(1)
        self._observable = ReplaySubject(1)
        self._stream = Stream(self._descriptor, self._observable)

    @property
    def stream(self) -> Stream:
        return self._stream

    def open(self):
        self._descriptor.on_error(self._exc)
        self._observable.on_error(self._exc)

    def close(self):
        pass


class Controller(QObject):
    config_changed = Signal(object)  # AppConfig

    def __init__(self, source_types: Dict[str, ISourceType], pipeline_types: Dict[str, IPipelineType], widget_service: WidgetService):
        super().__init__()

        self.source_types = source_types
        self.pipeline_types = pipeline_types
        self.widget_service = widget_service

        self.config = AppConfig()

        self.sources: Dict[str, ISource] = {}
        self.source_widget_handles: Dict[str, IVisualizerHandle] = {}

        self.preview_scheduler = EventLoopScheduler()

        self.pipeline = None
        self.stop = None

    def add_source(self, source_config: SourceConfig):
        assert source_config.id not in self.sources

        self.config.sources[source_config.id] = source_config
        self.config_changed.emit(deepcopy(self.config))
        self._setup_source(source_config.id)
        self._start_preview(source_config.id)

    def edit_source(self, source_config: SourceConfig):
        assert source_config.id in self.sources
        self.config.sources[source_config.id] = source_config
        self.config_changed.emit(deepcopy(self.config))

        self._stop_preview(source_config.id)
        self._teardown_source(source_config.id)
        self._setup_source(source_config.id)
        self._start_preview(source_config.id)

    def remove_source(self, source_id: str):
        assert source_id in self.sources

        self.config.sources.pop(source_id, None)
        self.config_changed.emit(deepcopy(self.config))

        self._stop_preview(source_id)
        self._teardown_source(source_id)

    def setup_source(self, source_id: str):
        print("setup source", source_id)

        self._stop_preview(source_id)
        self._teardown_source(source_id)
        self._setup_source(source_id)
        self._start_preview(source_id)

    def edit_pipeline(self, pipeline_config: PipelineConfig):
        print(pipeline_config)
        if self.pipeline:
            self.pipeline.dispose()
        pipeline_type = self.pipeline_types.get(pipeline_config.pipeline_type)
        self.pipeline = pipeline_type.get_pipeline_factory()()
        self.pipeline.configure(AppContext(self.widget_service), pipeline_config.active_config)

    def start_recording(self, group_id: str, session_id: str):
        print(f"Starting recording for group {group_id} session {session_id}")
        from reactivex import operators as ops

        source = self.sources.get(group_id)
        start = Subject()
        self.stop = Subject()

        obs = source.stream.observable.pipe(ops.publish())
        gated_source = Stream(source.stream.descriptor, obs.pipe(ops.skip_until(start), ops.take_until(self.stop)))

        print("Building pipeline...")
        self.pipeline.build(AppContext(self.widget_service), [gated_source])
        print("Pipeline built")

        print("Connecting...")
        obs.connect()
        print("Connected")

        start.on_next(None)

    def stop_recording(self, group_id: str):
        self.stop.on_next(None)

    def _setup_source(self, source_id: str):
        source_config = self.config.sources.get(source_id)
        assert source_config is not None

        source_type = self.source_types.get(source_config.source_type)
        assert source_type is not None

        if source_id in self.sources:
            self._teardown_source(source_id)

        try:
            source_factory = source_type.get_source_factory()
            source = source_factory(source_config.active_config)
        except Exception as e:
            print(f"Error setting up source {source_id}: {e}")
            source = ErrorSource(e)

        self.sources[source_id] = source

        source.open()

    def _teardown_source(self, source_id: str):
        source = self.sources.pop(source_id, None)
        if source:
            source.close()

    def _start_preview(self, source_id: str):
        source_config = self.config.sources.get(source_id)
        assert source_config is not None

        source_type = self.source_types.get(source_config.source_type)
        assert source_type is not None

        source = self.sources.get(source_id)
        assert source is not None

        session_id = str(uuid.uuid4())
        source_widget_handle = self.widget_service.get_visualizer_handle(source_type.visualizer_type, source_id, session_id, is_source=True)
        self.source_widget_handles[source_id] = source_widget_handle

        source_widget_handle.subscribe(source.stream)

    def _stop_preview(self, source_id: str):
        source_widget_handle = self.source_widget_handles.pop(source_id, None)
        if source_widget_handle:
            source_widget_handle.unsubscribe()
            source_widget_handle.dispose()
