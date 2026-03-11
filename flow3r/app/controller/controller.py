import uuid
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Iterator, List, Tuple, Any, Set

from PySide6.QtCore import QObject, Signal, Slot, Qt
import reactivex as rx
from reactivex import Subject
from reactivex.abc import DisposableBase
from reactivex.disposable import Disposable
from reactivex.scheduler import EventLoopScheduler

from flow3r.app.api.app.session_context import SessionContext
from flow3r.app.api.app.settings_view import SettingsView
from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.group_config import GroupConfig
from flow3r.app.controller.commit import ConfigChangeReply
from flow3r.app.controller.session_state import SessionStateBase, Finished, FinishingProcessing, FinishingRecording, Running, \
    Ready, NotReady
from flow3r.app.api.app.widget_service import WidgetService, SessionWidgetServiceWrapper
from flow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription, CompositePipelineSubscription, \
    PreviewSubscription, CompositePreviewSubscription
from flow3r.core.pipeline.abc.pipeline_type import IPipelineType
from flow3r.core.pipeline.pipeline_config import PipelineConfig
from flow3r.core.placeholder.simple_placeholder_provider import SimplePlaceholderProvider
from flow3r.core.source.abc.source import ISource
from flow3r.core.source.abc.source_type import ISourceType
from flow3r.app.config.source_config import SourceConfig
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


class ErrorSource(ISource):
    def __init__(self, exc: Exception):
        self._exc = exc
        self._stream = Stream(None, rx.throw(exc))

    @property
    def stream(self) -> Stream:
        return self._stream

    def open(self):
        pass

    def close(self):
        pass


@dataclass
class SourceEntry:
    name: str = ""
    source: Optional[ISource] = None
    widget_handle: Optional[IVisualizerHandle] = None
    preview_sub: Optional[DisposableBase] = None


@dataclass
class Preview:
    connections: List[DisposableBase]
    preview_sub: Optional[PreviewSubscription]


@dataclass
class Recording:
    start: Subject
    stop: Subject
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    connections: Optional[List[DisposableBase]] = None
    pipeline_sub: Optional[PipelineSubscription] = None
    primary_finished: bool = False
    secondary_finished: bool = False
    finished: bool = False
    progress: Tuple[int, int] = (0, 0)


@dataclass
class Session:
    group_id: str
    session_id: str
    group_name: str
    recording_number: int
    recording_duration: Optional[float] = None
    recording: Optional[Recording] = None

    def get_placeholder_provider(self) -> SimplePlaceholderProvider:
        start_time = self.recording.start_time if self.recording and self.recording.start_time else datetime.now()
        return SimplePlaceholderProvider({
            "group_name": self.group_name,
            "recording_number": self.recording_number,
            "start_time": start_time.strftime("%Y%m%d%H%M%S")
        })


@dataclass
class Group:
    group_id: str
    group_name: str
    sessions: Dict[str, Session] = field(default_factory=dict)
    recording_number: int = 0
    recording_duration: Optional[float] = None
    active_session_id: Optional[str] = None
    pipelines: Dict[str, IPipeline] = field(default_factory=dict)
    preview: Optional[Preview] = None

    @property
    def active_session(self) -> Optional[Session]:
        return self.sessions[self.active_session_id] if self.active_session_id else None

    def new_session(self, active: bool = True):
        self.recording_number += 1
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(self.group_id, session_id, self.group_name, self.recording_number, self.recording_duration)
        if active:
            self.active_session_id = session_id
        return session_id


@dataclass(frozen=True)
class ChangeSet:
    settings_changed: Dict[Tuple[str, ...], Any]

    # groups
    groups_added: Dict[str, GroupConfig]
    groups_removed: Dict[str, GroupConfig]
    groups_updated: Dict[str, Tuple[GroupConfig, GroupConfig]]  # (old, new)

    # sources
    sources_added: Dict[str, SourceConfig]
    sources_removed: Dict[str, SourceConfig]
    sources_updated: Dict[str, Tuple[SourceConfig, SourceConfig]]

    # pipelines
    pipelines_added: Dict[str, PipelineConfig]
    pipelines_removed: Dict[str, PipelineConfig]
    pipelines_updated: Dict[str, Tuple[PipelineConfig, PipelineConfig]]

    # derived / important semantic changes
    source_name_changed: List[Tuple[str, str]]  # source_id, new_name
    source_group_changed: List[Tuple[str, Optional[str], Optional[str]]]  # source_id, old_gid, new_gid

    group_name_changed: List[Tuple[str, str]]

    group_pipeline_added: Set[Tuple[str, str]]
    group_pipeline_removed: Set[Tuple[str, str]]
    group_pipeline_updated: Set[Tuple[str, str]]

    group_recording_duration_changed: Dict[str, Tuple[Optional[float], Optional[float]]]

    group_controls_changed: List[Tuple[str, str, Optional[str]]]  # group_id


def diff_by_id(old_map: Dict[str, Any], new_map: Dict[str, Any]):
    old_ids = set(old_map)
    new_ids = set(new_map)

    added_ids = new_ids - old_ids
    removed_ids = old_ids - new_ids
    kept_ids = old_ids & new_ids

    added = {_id: new_map[_id] for _id in added_ids}
    removed = {_id: old_map[_id] for _id in removed_ids}
    updated = {
        _id: (old_map[_id], new_map[_id])
        for _id in kept_ids
        if old_map[_id] != new_map[_id]
    }
    return added, removed, updated


def determine_location(sources: List[SourceConfig], pipelines: List[PipelineConfig]) -> Tuple[str, Optional[str]]:
    if len(sources) == 0 or len(pipelines) == 0:
        return "hidden", None
    elif len(sources) == 1:
        #return "source", sources[0].id
        return "bottom", None
    else:
        return "bottom", None


def diff_config(old: AppConfig, new: AppConfig) -> ChangeSet:
    settings_changed = {k: v for k, v in new.settings.items() if old.settings.get(k) != v}

    groups_added, groups_removed, groups_updated = diff_by_id(old.all_groups, new.all_groups)
    sources_added, sources_removed, sources_updated = diff_by_id(old.sources, new.sources)
    pipelines_added, pipelines_removed, pipelines_updated = diff_by_id(old.pipelines, new.pipelines)

    for pipeline_config in new.pipelines.values():
        if pipeline_config.id not in old.pipelines:
            continue

        settings_dependencies = pipeline_config.active_config.settings_dependencies
        if any(dep in settings_changed for dep in settings_dependencies):
            pipelines_updated[pipeline_config.id] = (old.pipelines[pipeline_config.id], pipeline_config)

    # semantic changes you care about (these drive runtime operations)
    source_name_changed: List[Tuple[str, str]] = []
    for old_sc, new_sc in sources_updated.values():
        if old_sc.name != new_sc.name:
            source_name_changed.append((new_sc.id, new_sc.name))

    source_group_changed: List[Tuple[str, Optional[str], Optional[str]]] = []
    for old_sc, new_sc in sources_updated.values():
        if old_sc.group_id != new_sc.group_id:
            source_group_changed.append((new_sc.id, old_sc.group_id, new_sc.group_id))

    group_name_changed: List[Tuple[str, str]] = []
    for old_gc, new_gc in groups_updated.values():
        if old_gc.name != new_gc.name:
            group_name_changed.append((new_gc.id, new_gc.name))

    group_pipeline_added: Set[Tuple[str, str]] = set()
    group_pipeline_removed: Set[Tuple[str, str]] = set()
    group_pipeline_updated: Set[Tuple[str, str]] = set()
    for old_gc, new_gc in groups_updated.values():
        for pipeline_id in new_gc.pipeline_ids:
            if pipeline_id not in old_gc.pipeline_ids:
                group_pipeline_added.add((new_gc.id, pipeline_id))
        for pipeline_id in old_gc.pipeline_ids:
            if pipeline_id not in new_gc.pipeline_ids:
                group_pipeline_removed.add((new_gc.id, pipeline_id))

    for new_gc in new.all_groups.values():
        old_gc = old.all_groups.get(new_gc.id)
        if old_gc is None:
            continue
        for pipeline_id in new_gc.pipeline_ids:
            if pipeline_id in old_gc.pipeline_ids and pipeline_id in pipelines_updated:
                group_pipeline_updated.add((new_gc.id, pipeline_id))

    group_recording_duration_changed: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    for gc in groups_added.values():
        new_duration = gc.recording_config.recording_duration if gc.recording_config.recording_mode == "timed" else None
        group_recording_duration_changed[gc.id] = (None, new_duration)

    for old_gc, new_gc in groups_updated.values():
        old_duration = old_gc.recording_config.recording_duration if old_gc.recording_config.recording_mode == "timed" else None
        new_duration = new_gc.recording_config.recording_duration if new_gc.recording_config.recording_mode == "timed" else None
        if old_duration != new_duration:
            group_recording_duration_changed[new_gc.id] = (old_duration, new_duration)

    group_controls_changed: List[Tuple[str, str, Optional[str]]] = []
    for gid, new_gc in new.all_groups.items():
        old_sources = [sc for sc in old.sources.values() if sc.group_id == gid or sc.id == gid]
        new_sources = [sc for sc in new.sources.values() if sc.group_id == gid or sc.id == gid]

        old_gc = old.all_groups.get(gid)
        old_pipelines = [pc for pc in old.pipelines.values() if pc.id in old_gc.pipeline_ids] if old_gc else []
        new_pipelines = [pc for pc in new.pipelines.values() if pc.id in new_gc.pipeline_ids]

        old_location, old_source_id = determine_location(old_sources, old_pipelines)
        new_location, new_source_id = determine_location(new_sources, new_pipelines)

        if gid in [g.id for g in groups_added.values()] or old_location != new_location or old_source_id != new_source_id:
            group_controls_changed.append((gid, new_location, new_source_id))


    return ChangeSet(
        settings_changed=settings_changed,

        groups_added=groups_added,
        groups_removed=groups_removed,
        groups_updated=groups_updated,

        sources_added=sources_added,
        sources_removed=sources_removed,
        sources_updated=sources_updated,

        pipelines_added=pipelines_added,
        pipelines_removed=pipelines_removed,
        pipelines_updated=pipelines_updated,

        source_name_changed=source_name_changed,
        source_group_changed=source_group_changed,
        group_name_changed=group_name_changed,

        group_pipeline_added=group_pipeline_added,
        group_pipeline_removed=group_pipeline_removed,
        group_pipeline_updated=group_pipeline_updated,

        group_recording_duration_changed=group_recording_duration_changed,

        group_controls_changed=group_controls_changed
    )


class Controller(QObject):
    log_message = Signal(str)

    settings_snapshot = Signal(object)  # settings state
    settings_changed = Signal(object)  # subset of state that changed

    config_snapshot = Signal(AppConfig)
    config_changed = Signal(AppConfig)  # AppConfig

    config_change_failed = Signal(object)  # Exception

    source_snapshot = Signal(SourceConfig)
    source_added = Signal(SourceConfig)
    source_changed = Signal(SourceConfig)
    source_removed = Signal(str)

    group_snapshot = Signal(GroupConfig)
    group_added = Signal(GroupConfig)
    group_changed = Signal(GroupConfig)
    group_removed = Signal(str)

    pipeline_added = Signal(PipelineConfig)
    pipeline_changed = Signal(PipelineConfig)
    pipeline_removed = Signal(str)

    active_session_snapshot = Signal(str, str, SessionStateBase)  # group_id, session_id, state
    active_session_changed = Signal(str, str, SessionStateBase)  # group_id, session_id, state
    session_state_changed = Signal(str, str, SessionStateBase)  # group_id, session_id, state

    primary_finished = Signal(str, str, object)  # group_id, session_id, exc
    secondary_finished = Signal(str, str, object)  # group_id, session_id, exc
    progress_updated = Signal(str, str, object)  # group_id, session_id, progress

    config_loaded = Signal(object)  # window layout

    def __init__(self, source_types: Dict[str, ISourceType], pipeline_types: Dict[str, IPipelineType], widget_service: WidgetService):
        super().__init__()

        self.source_types = source_types
        self.pipeline_types = pipeline_types
        self.widget_service = widget_service

        self._config = AppConfig()
        self._draft: Optional[AppConfig] = None
        self._in_tx = 0

        self.preview_scheduler = EventLoopScheduler()

        self.sources: Dict[str, SourceEntry] = {}
        self.groups: Dict[str, Group] = {}

        self.primary_finished.connect(self._primary_finished, Qt.ConnectionType.QueuedConnection)
        self.secondary_finished.connect(self._secondary_finished, Qt.ConnectionType.QueuedConnection)
        self.progress_updated.connect(self._progress_updated, Qt.ConnectionType.QueuedConnection)

    @property
    def config(self) -> AppConfig:
        return deepcopy(self._config)

    @contextmanager
    def transaction(self, reply: Optional[ConfigChangeReply] = None) -> Iterator[AppConfig]:
        if self._in_tx != 0:
            # simplest option: allow nesting by reusing same draft
            self._in_tx += 1
            try:
                yield self._draft  # type: ignore
            finally:
                self._in_tx -= 1
            return

        self._in_tx = 1
        self._draft = deepcopy(self._config)
        try:
            assert self._draft is not None
            yield self._draft
            # commit only at outermost
            self._commit(self._draft)
            if reply:
                reply.finished.emit(True, None)
        except Exception as exc:
            self.config_change_failed.emit(exc)
            if reply:
                reply.finished.emit(False, exc)
        finally:
            self._draft = None
            self._in_tx = 0

    def _commit(self, new_config: AppConfig):
        old_config = self._config

        self._repair_config(new_config)
        self._validate_config(new_config)

        changes = diff_config(old_config, new_config)

        self._check_permission(changes)

        # Apply runtime effects in one place
        try:
            self._apply_changes(changes, old_config, new_config)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

        # Update stored config last (or first, but be consistent)
        self._config = new_config

        # Emit signals (single source of truth)
        self.config_changed.emit(deepcopy(self._config))
        self._emit_entity_signals(changes)

    @Slot()
    def send_settings_snapshot(self) -> None:
        self.settings_snapshot.emit(deepcopy(self._config.settings))

    @Slot()
    def send_config_snapshot(self):
        self.config_snapshot.emit(deepcopy(self.config))

    @Slot(str)
    def send_source_snapshot(self, source_id: str):
        self.source_snapshot.emit(deepcopy(self.config.sources[source_id]))

    @Slot(str)
    def send_group_snapshot(self, group_id: str):
        self.group_snapshot.emit(deepcopy(self.config.all_groups[group_id]))

    @Slot(str)
    def send_active_session_snapshot(self, group_id: str):
        group = self.groups.get(group_id)
        if group and group.active_session_id:
            state = self._get_session_state(group_id, group.active_session_id)
            self.active_session_snapshot.emit(group_id, group.active_session_id, state)

    @Slot(object)
    def set_settings(self, patch: Dict[Tuple[str, ...], Any]) -> None:
        assert all(isinstance(k, tuple) for k in patch.keys())

        # apply changes
        with self.transaction() as config:
            print(f"set_settings: {patch}")
            for key_path, value in patch.items():
                config.settings[key_path] = deepcopy(value)

    @Slot(object)
    def add_source(self, source_config: SourceConfig, reply: Optional[ConfigChangeReply] = None):
        with self.transaction(reply) as config:
            assert source_config.id not in config.sources
            config.sources[source_config.id] = source_config

    @Slot(object)
    def edit_source(self, source_config: SourceConfig):
        with self.transaction() as config:
            assert source_config.id in config.sources

            config.sources[source_config.id] = source_config

    @Slot(str)
    def remove_source(self, source_id: str):
        with self.transaction() as config:
            assert source_id in config.sources

            config.sources.pop(source_id, None)
            config.implicit_groups.pop(source_id, None)

    @Slot(str)
    def setup_source(self, source_id: str):
        config = self.config

        source_config = config.sources[source_id]

        self._stop_pipeline_preview(source_config.implicit_group_id)

        self._stop_preview(source_id)
        self._teardown_source(source_id)

        self._setup_source(source_config)
        self._start_preview(source_config)

        self._start_pipeline_preview(config, source_config.implicit_group_id)

    @Slot(object)
    def add_group(self, group_config: GroupConfig):
        with self.transaction() as config:
           assert group_config.id not in config.groups

           config.groups[group_config.id] = group_config

    @Slot(object)
    def edit_group(self, group_config: GroupConfig):
        with self.transaction() as config:
            assert group_config.id in config.all_groups

            if group_config.id in config.groups:
                config.groups[group_config.id] = group_config
            elif group_config.id in config.implicit_groups:
                config.implicit_groups[group_config.id] = group_config

    @Slot(str)
    def remove_group(self, group_id: str):
        with self.transaction() as config:
            assert group_id in config.groups

            config.groups.pop(group_id, None)

    @Slot(str, object)
    def assign_group(self, source_id: str, group_id: Optional[str]):
        with self.transaction() as config:
            assert source_id in config.sources, f"SourceConfig {source_id} not found"
            assert group_id is None or group_id in config.groups, f"GroupConfig {group_id} not found"

            source_config = config.sources[source_id]
            source_config.group_id = group_id

    @Slot(object)
    def add_pipeline(self, pipeline_config: PipelineConfig):
        with self.transaction() as config:
            assert pipeline_config.id not in config.pipelines

            config.pipelines[pipeline_config.id] = pipeline_config

    @Slot(object)
    def edit_pipeline(self, pipeline_config: PipelineConfig):
        with self.transaction() as config:
            assert pipeline_config.id in config.pipelines

            config.pipelines[pipeline_config.id] = pipeline_config

    @Slot(str)
    def remove_pipeline(self, pipeline_id: str):
        with self.transaction() as config:
            assert pipeline_id in config.pipelines

            config.pipelines.pop(pipeline_id, None)

    @Slot(str, object)
    def assign_pipeline_to_source(self, source_id: str, pipeline_id: Optional[str]):
        with self.transaction() as config:
            assert source_id in config.sources
            assert source_id in config.implicit_groups

            if pipeline_id is None:
                self.set_pipeline_assignment(source_id, set(), {})
                return

            assert pipeline_id in config.pipelines

            source_config = config.sources[source_id]
            pipeline_config = config.pipelines[pipeline_id]

            assert len(pipeline_config.active_config.inputs) == 1
            input_name = pipeline_config.active_config.inputs[0]

            pipeline_ids = {pipeline_id}
            input_mapping = {pipeline_id: {input_name: source_config.id}}
            self.set_pipeline_assignment(source_id, pipeline_ids, input_mapping)

    @Slot(str, object, object)
    def set_pipeline_assignment(self, group_id: str, pipeline_ids: Set[str], source_mapping: Optional[Dict[str, Dict[str, str]]] = None):
        with self.transaction() as config:
            assert group_id in config.all_groups
            assert all(pipeline_id in config.pipelines for pipeline_id in pipeline_ids)

            group_config = config.all_groups[group_id]
            group_config.pipeline_ids = pipeline_ids
            group_config.source_mapping = source_mapping or {}

    @Slot(str, str)
    def start_recording(self, group_id: str, session_id: str):
        print(f"start_recording({group_id}, {session_id})")
        group_config = self.config.all_groups[group_id]
        source_configs = [sc for sc in self.config.sources.values() if sc.group_id == group_id]

        assert len(group_config.pipeline_ids) > 0
        pipeline_configs = [self.config.pipelines[pipeline_id] for pipeline_id in group_config.pipeline_ids]

        group = self.groups[group_id]

        assert all(pc.id in group.pipelines for pc in pipeline_configs), f"Not all pipelines set up for group {group_id}"
        assert all(
            len(pc.active_config.inputs) == len(source_configs) == 1 or \
            all(input_name in group_config.source_mapping[pc.id] for input_name in pc.active_config.inputs)
            for pc in pipeline_configs
        ), f"Not inputs have a source assigned for group {group_id}"

        if group.preview:
            self._stop_pipeline_preview(group_id)

        session = group.sessions[session_id]

        if session.recording and session.recording.start_time:
            return

        from reactivex import operators as ops

        start = Subject()
        stop = Subject()
        session.recording = Recording(start, stop)

        source_observables = []
        source_streams: Dict[str, Dict[str, Stream]] = {}
        for pipeline_config in pipeline_configs:
            if pipeline_config.id not in source_streams:
                source_streams[pipeline_config.id] = {}

            if len(pipeline_config.active_config.inputs) == len(source_configs) == 1:
                input_name = pipeline_config.active_config.inputs[0]
                source_config = source_configs[0]
                source = self.sources[source_config.id]
                format = source.source.stream.format
                observable = source.source.stream.data.pipe(ops.publish())
                source_observables.append(observable)
                gated_observable = observable.pipe(ops.skip_until(session.recording.start), ops.take_until(session.recording.stop))
                source_streams[pipeline_config.id][input_name] = Stream(format, gated_observable, name=source.name)
            else:
                for input_name in pipeline_config.active_config.inputs:
                    source_id = group_config.source_mapping[pipeline_config.id][input_name]
                    source = self.sources[source_id]
                    format = source.source.stream.format
                    observable = source.source.stream.data.pipe(ops.publish())
                    source_observables.append(observable)
                    gated_observable = observable.pipe(ops.skip_until(session.recording.start), ops.take_until(session.recording.stop))
                    source_streams[pipeline_config.id][input_name] = Stream(format, gated_observable, name=source.name)

        start_time = datetime.now()

        try:
            session.recording.start_time = start_time
            placeholder_provider = session.get_placeholder_provider()

            widget_service = SessionWidgetServiceWrapper(self.widget_service, group_id, session_id)
            settings_view = SettingsView(self.config.settings)
            session_context = SessionContext(widget_service, settings_view)

            pipeline_subs = []
            for pipeline_config in pipeline_configs:
                pipeline = group.pipelines[pipeline_config.id]
                #pipeline.configure(session_context, pipeline_config.active_config.resolve(placeholder_provider))
                sub = pipeline.build(session_context, source_streams[pipeline_config.id])
                pipeline_subs.append(sub)

            session.recording.pipeline_sub = CompositePipelineSubscription(pipeline_subs)

        except:
            print(self.config)
            raise

        def _primary_done(_):
            print("Primary done")
            self.primary_finished.emit(group_id, session_id, None)

        def _primary_failed(exc: Exception):
            print(f"Primary failed: {exc}")
            self.primary_finished.emit(group_id, session_id, exc)

        def _secondary_done(_):
            self.secondary_finished.emit(group_id, session_id, None)

        def _secondary_failed(exc: Exception):
            self.secondary_finished.emit(group_id, session_id, exc)

        def _progress_updated(progress: Tuple[int, int]):
            self.progress_updated.emit(group_id, session_id, progress)

        session.recording.pipeline_sub.primary_done.pipe(ops.take(1)).subscribe(_primary_done, _primary_failed)
        session.recording.pipeline_sub.secondary_done.pipe(ops.take(1)).subscribe(_secondary_done, _secondary_failed)
        if session.recording.pipeline_sub.progress:
            session.recording.pipeline_sub.progress.subscribe(_progress_updated)

        session.recording.connections = []
        for obs in source_observables:
            sub = obs.connect()
            session.recording.connections.append(sub)

        session.recording.start.on_next(None)
        self._update_session_state(group_id, session_id)

    @Slot(str, str)
    def stop_recording(self, group_id: str, session_id: str):
        print(f"stop_recording({group_id}, {session_id})")

        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if session.recording and not session.recording.stop_time:
            session.recording.stop_time = datetime.now()
            print("Sending stop signal to recording pipeline.")
            session.recording.stop.on_next(None)

        self._update_session_state(group_id, session_id)

    @Slot(str, str, object)
    def _primary_finished(self, group_id: str, session_id: str, exc: Optional[Exception]):
        print(f"_primary_finished({group_id}, {session_id}, {exc})")
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if session.recording:
            if session.recording.primary_finished:
                return

            print("Session primary done.")
            session.recording.primary_finished = True

            if session.recording.secondary_finished:
                self._recording_finished(group_id, session_id)

        self._update_session_state(group_id, session_id)

    @Slot(str, str, object)
    def _secondary_finished(self, group_id: str, session_id: str, exc: Optional[Exception]):
        print(f"_secondary_finished({group_id}, {session_id}, {exc})")
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if session.recording:
            if session.recording.secondary_finished:
                return

            print("Session secondary done.")
            session.recording.secondary_finished = True

            if session.recording.primary_finished:
                self._recording_finished(group_id, session_id)

        self._update_session_state(group_id, session_id)

    @Slot(str, str, object)
    def _progress_updated(self, group_id: str, session_id: str, progress: Tuple[int, int]):
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if session.recording:
            session.recording.progress = progress

        self._update_session_state(group_id, session_id)

    @Slot(str, str)
    def _recording_finished(self, group_id: str, session_id: str):
        print(f"_recording_finished({group_id}, {session_id})")

        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if not session.recording:
            return

        if session.recording.finished:
            return

        session.recording.finished = True

        session.recording.pipeline_sub.dispose()

        for connection_sub in session.recording.connections:
            connection_sub.dispose()

        group.new_session()
        self._update_active_session(group_id)
        self._update_session_state(group_id, session_id)

        self._start_pipeline_preview(self.config, group_id)

    def _pipeline_input_mapping(self, config: AppConfig, group_id: str, pipeline_id: str) -> Dict[str, str]:
        group_config = config.all_groups[group_id]
        pipeline_config = config.pipelines[pipeline_id]

        source_configs = [sc for sc in config.sources.values() if sc.implicit_group_id == group_id]

        if len(pipeline_config.active_config.inputs) == len(source_configs) == 1:
            input_name = pipeline_config.active_config.inputs[0]
            source_config = source_configs[0]
            return {input_name: source_config.id}
        else:
            return group_config.source_mapping[pipeline_config.id]

    def _start_pipeline_preview(self, app_config: AppConfig, group_id: str):
        group_config = app_config.all_groups[group_id]
        source_configs = [sc for sc in app_config.sources.values() if sc.group_id == group_id]

        if not len(group_config.pipeline_ids) > 0:
            return
        pipeline_configs = [app_config.pipelines[pipeline_id] for pipeline_id in group_config.pipeline_ids]

        group = self.groups[group_id]

        if group.preview:
            return

        assert all(pc.id in group.pipelines for pc in pipeline_configs), f"Not all pipelines set up for group {group_id}"
        if not all(
            len(pc.active_config.inputs) == len(source_configs) == 1 or \
            all(input_name in group_config.source_mapping[pc.id] for input_name in pc.active_config.inputs)
            for pc in pipeline_configs
        ):
            return

        from reactivex import operators as ops

        source_observables = []

        source_streams: Dict[str, Dict[str, IStream]] = {}
        for pipeline_config in pipeline_configs:
            if pipeline_config.id not in source_streams:
                source_streams[pipeline_config.id] = {}

            input_mapping = self._pipeline_input_mapping(app_config, group_id, pipeline_config.id)

            for input_name in pipeline_config.active_config.inputs:
                source_id = input_mapping[input_name]
                source = self.sources[source_id]
                format = source.source.stream.format
                observable = source.source.stream.data.pipe(ops.publish())
                source_observables.append(observable)
                source_streams[pipeline_config.id][input_name] = Stream(format, observable, source.name)

        try:
            widget_service = SessionWidgetServiceWrapper(self.widget_service, group_id, "preview")
            settings_view = SettingsView(app_config.settings)
            session_context = SessionContext(widget_service, settings_view)

            preview_subs = []
            for pipeline_config in pipeline_configs:
                pipeline = group.pipelines[pipeline_config.id]
                try:
                    sub = pipeline.preview(session_context, source_streams[pipeline_config.id])
                except Exception as e:
                    import traceback
                    traceback.print_exc()

                    sub = PreviewSubscription(Disposable(), rx.from_(True))

                preview_subs.append(sub)

            preview_sub = CompositePreviewSubscription(preview_subs)

        except:
            raise

        def _preview_done(_):
            print("Preview done")

        def _preview_failed(exc: Exception):
            print(f"Preview primary failed: {exc}")

        preview_sub.done.pipe(ops.take(1)).subscribe(_preview_done, _preview_failed)

        connections = []
        for obs in source_observables:
            sub = obs.connect()
            connections.append(sub)

        group.preview = Preview(connections, preview_sub)

    def _stop_pipeline_preview(self, group_id: str):
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        preview = group.preview

        if preview is None:
            return

        preview.preview_sub.dispose()
        print("Disposed preview subscription")
        for connection in preview.connections:
            connection.dispose()
        group.preview = None

    def _repair_config(self, config: AppConfig):
        self._remove_non_existant_references(config)
        self._update_implicit_groups(config)

    def _remove_non_existant_references(self, config: AppConfig):
        for source_config in config.sources.values():
            if source_config.group_id is not None and source_config.group_id not in config.groups:
                source_config.group_id = None

        for group_config in config.all_groups.values():
            group_config.pipeline_ids = set(pcid for pcid in group_config.pipeline_ids if pcid in config.pipelines)

            group_sources = {sc.id for sc in config.sources.values() if sc.implicit_group_id == group_config.id}
            group_config.source_mapping = {
                pid: {
                    input_name: source_id
                    for input_name, source_id in mapping.items()
                    if input_name in config.pipelines[pid].active_config.inputs and source_id in group_sources
                }
                for pid, mapping in group_config.source_mapping.items()
                if pid in group_config.pipeline_ids
            }

    def _update_implicit_groups(self, config: AppConfig):
        for source_id, source_config in config.sources.items():
            if source_config.group_id is None:
                group_name = source_config.name
                if source_id not in config.implicit_groups:
                    config.implicit_groups[source_id] = GroupConfig(id=source_id, name=group_name, implicit=True)
                elif config.implicit_groups[source_id].name != group_name:
                    config.implicit_groups[source_id].name = group_name

        implicit_groups_to_remove = set()
        for source_id in config.implicit_groups:
            if source_id not in config.sources or config.sources[source_id].group_id is not None:
                implicit_groups_to_remove.add(source_id)

        for source_id in implicit_groups_to_remove:
            config.implicit_groups.pop(source_id)

    def _validate_config(self, config: AppConfig):
        #if random.random() < 0.1:
        #    raise Exception("Random validation error")

        return None

    def _check_permission(self, changes: ChangeSet):
        changed_sources = [source_config for _, source_config in changes.sources_updated.values()]
        changed_sources += [source_config for source_config in changes.sources_removed.values()]
        for source_config in changed_sources:
            group = self.groups[source_config.implicit_group_id]
            if any(session.recording and session.recording.start_time and not session.recording.finished for session in group.sessions.values()):
                raise Exception("Cannot edit source while it is used in a recording")

    def _apply_changes(self, changes: ChangeSet, old: AppConfig, new: AppConfig):
        sources_requiring_rebuild = {
            new_sc.id: new_sc for old_sc, new_sc in changes.sources_updated.values()
            if self._source_requires_rebuild(old_sc, new_sc)
        }
        
        groups_requiring_preview_stop = set()
        groups_requiring_preview_start = set()
        for group_id in changes.groups_removed:
            groups_requiring_preview_stop.add(group_id)

        # TODO: preview is started mid-recording when settings are changed :(
        for group_id in new.all_groups:
            if group_id in changes.groups_added:
                groups_requiring_preview_start.add(group_id)
            elif any(group_id == gid for gid, pid in changes.group_pipeline_updated):
                groups_requiring_preview_stop.add(group_id)
                groups_requiring_preview_start.add(group_id)
            else:
                old_group_config = old.all_groups[group_id]
                new_group_config = new.all_groups[group_id]

                old_source_ids = {sc.id for sc in old.sources.values() if sc.implicit_group_id == group_id}
                new_source_ids = {sc.id for sc in new.sources.values() if sc.implicit_group_id == group_id}
                
                if old_group_config.pipeline_ids != new_group_config.pipeline_ids \
                    or old_group_config.source_mapping != new_group_config.source_mapping \
                    or old_source_ids != new_source_ids \
                    or any(new_sc.id in sources_requiring_rebuild for new_sc in new.sources.values()):
                    groups_requiring_preview_stop.add(group_id)
                    groups_requiring_preview_start.add(group_id)

        for group_id in groups_requiring_preview_stop:
            print(f"Stopping preview for group {group_id}")
            self._stop_pipeline_preview(group_id)

        # --- 2) teardown removed sources/groups (sources first if they depend on groups) ---
        for sid in changes.sources_removed:
            self._stop_preview(sid)
            self._teardown_source(sid)
            self._teardown_source_widget(sid)

        for source_id in sources_requiring_rebuild:
            self._stop_preview(source_id)
            self._teardown_source(source_id)

        for gid in changes.groups_removed:
            self._teardown_group(gid)

        # --- 3) create added groups/sources ---
        for group_config in changes.groups_added.values():
            self._setup_group(group_config)

        for source_config in changes.sources_added.values():
            self._setup_source_widget(source_config)
            self._setup_source(source_config)

        for group_config in new.all_groups.values():
            self._ensure_active_session(group_config.id)

        sessions_to_update = set()
        for group_id, group_name in changes.group_name_changed:
            group = self.groups[group_id]
            group.name = group_name
            sessions_to_update.add((group_id, group.active_session_id))

        for group_id, (old_duration, new_duration) in changes.group_recording_duration_changed.items():
            group = self.groups[group_id]
            group.recording_duration = new_duration
            group.active_session.recording_duration = new_duration
            sessions_to_update.add((group_id, group.active_session_id))

        # --- 4) apply updates ---
        for group_id in changes.groups_added:
            for pipeline_id in new.all_groups[group_id].pipeline_ids:
                self._setup_pipeline(new, group_id, pipeline_id)

        for group_id, pipeline_id in changes.group_pipeline_updated:
            old_pipeline_config, new_pipeline_config = old.pipelines[pipeline_id], new.pipelines[pipeline_id]
            if old_pipeline_config.pipeline_type == new_pipeline_config.pipeline_type:
                self._configure_pipeline(new, group_id, pipeline_id)
            else:
                self._teardown_pipeline(group_id, pipeline_id)
                self._setup_pipeline(new, group_id, pipeline_id)

        for group_id, pipeline_id in changes.group_pipeline_added:
            self._setup_pipeline(new, group_id, pipeline_id)

        for group_id, pipeline_id in changes.group_pipeline_removed:
            self._teardown_pipeline(group_id, pipeline_id)

        for sc in sources_requiring_rebuild.values():
            self._setup_source(sc)

        # --- 5) restart previews for relevant sources ---
        for sc in sources_requiring_rebuild.values():
            self._start_preview(sc)

        for sc in changes.sources_added.values():
            self._start_preview(sc)

        for group_id in groups_requiring_preview_start:
            self._start_pipeline_preview(new, group_id)

        for gid, location, source_id in changes.group_controls_changed:
            self.widget_service.set_recording_controls_location(gid, location, source_id)

        for group_id, session_id in sessions_to_update:
            self._update_session_state(group_id, session_id)

    def _source_requires_rebuild(self, old_sc: SourceConfig, new_sc: SourceConfig) -> bool:
        return old_sc.active_config != new_sc.active_config

    def _setup_source_widget(self, source_config: SourceConfig):
        if source_config.id not in self.sources:
            self.sources[source_config.id] = SourceEntry()

        source_entry = self.sources[source_config.id]

        if not source_entry.widget_handle:
            source_entry.widget_handle = self.widget_service.get_source_handle(source_config.id, "preview")

    def _teardown_source_widget(self, source_id: str):
        source_entry = self.sources.pop(source_id, None)
        if not source_entry or not source_entry.widget_handle:
            return
        source_entry.widget_handle.dispose()
        source_entry.widget_handle = None

    def _setup_source(self, source_config: SourceConfig):
        if source_config.id not in self.sources:
            self.sources[source_config.id] = SourceEntry()

        source_entry = self.sources[source_config.id]
        source_entry.name = source_config.name

        source_type = self.source_types.get(source_config.source_type)
        assert source_type is not None

        try:
            source_factory = source_type.get_source_factory()
            source = source_factory(source_config.active_config)
        except Exception as e:
            source = ErrorSource(e)

        source_entry.source = source

        source.open()

    def _teardown_source(self, source_id: str):
        print(f"_teardown_source({source_id})")
        source_entry = self.sources.get(source_id, None)
        if not source_entry or not source_entry.source:
            return

        source_entry.source.close()
        source_entry.source = None

    def _setup_group(self, group_config: GroupConfig):
        if group_config.id not in self.groups:
            recording_duration = group_config.recording_config.recording_duration if group_config.recording_config.recording_mode == "timed" else None
            self.groups[group_config.id] = Group(group_config.id, group_config.name, recording_duration=recording_duration)
            print("Adding group controls:")
            self.widget_service.add_recording_controls(group_config.id)
            self.widget_service.set_recording_controls_location(group_config.id, "bottom")

    def _teardown_group(self, group_id: str):
        group = self.groups.pop(group_id, None)
        if group:
            self.widget_service.remove_recording_controls(group_id)
            for pipeline in group.pipelines.values():
                pipeline.dispose()

    def _start_preview(self, source_config: SourceConfig):
        source_type = self.source_types.get(source_config.source_type)
        assert source_type is not None

        source_entry = self.sources.get(source_config.id)
        assert source_entry is not None
        assert source_entry.source is not None
        assert source_entry.widget_handle is not None

        widget_handle = source_entry.widget_handle

        widget_handle.set_error(None)
        widget_handle.set_format(source_entry.source.stream.format)
        source_entry.preview_sub = source_entry.source.stream.data.subscribe(
            on_next=widget_handle.set_item,
            on_error=widget_handle.set_error,
            on_completed=lambda: widget_handle.set_completed(True)
        )

    def _stop_preview(self, source_id: str):
        print(f"_stop_preview({source_id})")
        source_entry = self.sources.get(source_id)

        if not source_entry:
            return

        if source_entry.preview_sub:
            print("Unsubscribing from source preview")
            source_entry.preview_sub.dispose()

    def _setup_pipeline(self, config: AppConfig, group_id: str, pipeline_id: str):
        assert pipeline_id in config.pipelines
        pipeline_config = config.pipelines[pipeline_id]

        assert group_id in self.groups
        group = self.groups[group_id]

        pipeline = group.pipelines.get(pipeline_config.id)
        assert pipeline is None

        pipeline_type = self.pipeline_types.get(pipeline_config.pipeline_type)
        pipeline_factory = pipeline_type.get_pipeline_factory()
        pipeline = pipeline_factory()
        group.pipelines[pipeline_config.id] = pipeline

        self._configure_pipeline(config, group_id, pipeline_id)

    def _configure_pipeline(self, config: AppConfig, group_id: str, pipeline_id: str):
        assert pipeline_id in config.pipelines
        pipeline_config = config.pipelines[pipeline_id]

        assert group_id in self.groups
        group = self.groups[group_id]

        pipeline = group.pipelines.get(pipeline_config.id)
        assert pipeline is not None

        placeholder_provider = group.active_session.get_placeholder_provider()

        widget_service = SessionWidgetServiceWrapper(self.widget_service, group_id, "preview")
        settings_view = SettingsView(config.settings)
        session_context = SessionContext(widget_service, settings_view)

        input_mapping = self._pipeline_input_mapping(config, group_id, pipeline_config.id)

        source_names: Dict[str, str] = {}
        for input_name in pipeline_config.active_config.inputs:
            source_id = input_mapping.get(input_name)
            if source_id is not None:
                source = self.sources[source_id]
                source_names[input_name] = source.name

        pipeline.configure(session_context, pipeline_config.active_config.resolve(placeholder_provider), source_names)

    def _teardown_pipeline(self, group_id: str, pipeline_id: str):
        group = self.groups[group_id]
        pipeline = group.pipelines.pop(pipeline_id, None)
        if pipeline:
            pipeline.dispose()

    def _ensure_active_session(self, group_id: str):
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"
        if group.active_session_id is None:
            group.new_session()
            self._update_active_session(group_id)

    def _get_session_state(self, group_id: str, session_id: str):
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if session.recording:
            start_time = session.recording.start_time
            stop_time = session.recording.stop_time
            duration = session.recording_duration
            if start_time:
                if stop_time:
                    if session.recording.primary_finished:
                        if session.recording.secondary_finished:
                            return Finished(recording_number=session.recording_number, start_time=start_time, stop_time=stop_time, end_time=None, duration=duration)
                        else:
                            return FinishingProcessing(recording_number=session.recording_number, start_time=start_time, stop_time=stop_time, duration=duration)
                    else:
                        return FinishingRecording(recording_number=session.recording_number, start_time=start_time, stop_time=stop_time, duration=duration)
                else:
                    return Running(recording_number=session.recording_number, start_time=start_time, duration=duration)
            else:
                return Ready(recording_number=session.recording_number, duration=duration)
        else:
            return Ready(recording_number=session.recording_number, duration=session.recording_duration)

    def _update_active_session(self, group_id: str):
        active_session_id = self.groups[group_id].active_session_id
        if active_session_id:
            state = self._get_session_state(group_id, active_session_id)
        else:
            state = NotReady(reason="No active session", recording_number=None)
        self.active_session_changed.emit(group_id, active_session_id, state)

    def _update_session_state(self, group_id: str, session_id: str):
        state = self._get_session_state(group_id, session_id)
        self.session_state_changed.emit(group_id, session_id, state)

    def _emit_entity_signals(self, changes: ChangeSet):
        if changes.settings_changed:
            self.settings_changed.emit(deepcopy(changes.settings_changed))

        for gc in changes.groups_added.values():
            self.group_added.emit(deepcopy(gc))
        for old_gc, new_gc in changes.groups_updated.values():
            self.group_changed.emit(deepcopy(new_gc))
        for gid in changes.groups_removed:
            self.group_removed.emit(gid)

        for sc in changes.sources_added.values():
            self.source_added.emit(deepcopy(sc))
        for old_sc, new_sc in changes.sources_updated.values():
            self.source_changed.emit(deepcopy(new_sc))
        for sid in changes.sources_removed:
            self.source_removed.emit(sid)

        for pc in changes.pipelines_added.values():
            self.pipeline_added.emit(deepcopy(pc))
        for old_pc, new_pc in changes.pipelines_updated.values():
            self.pipeline_changed.emit(deepcopy(new_pc))
        for pid in changes.pipelines_removed:
            self.pipeline_removed.emit(pid)

    @Slot(str, object)
    def save_config(self, config_file: str, ui_state: object):
        import pickle
        with open(config_file, "wb") as f:
            pickle.dump((self.config, ui_state), f)

    @Slot(str)
    def load_config(self, config_file: str):
        import pickle
        with open(config_file, "rb") as f:
            new_config, ui_state = pickle.load(f)

        with self.transaction() as config:
            config.settings = new_config.settings
            config.groups = new_config.groups
            config.implicit_groups = new_config.implicit_groups
            config.sources = new_config.sources
            config.pipelines = new_config.pipelines

        self.config_loaded.emit(ui_state)
