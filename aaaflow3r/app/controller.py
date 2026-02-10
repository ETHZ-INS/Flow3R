import uuid
from concurrent.futures import Future
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Iterator, List, Tuple, Any

from PySide6.QtCore import QObject, Signal
import reactivex as rx
from reactivex import Subject
from reactivex.scheduler import EventLoopScheduler

from aaaflow3r.app.api.app.app_context import AppContext
from aaaflow3r.app.config.app_config import AppConfig
from aaaflow3r.app.config.group_config import GroupConfig
from aaaflow3r.app.session_state import SessionStateBase, SessionState
from aaaflow3r.app.widget_service import WidgetService, SessionWidgetServiceWrapper
from aaaflow3r.core.pipeline.abc.pipeline import IPipeline
from aaaflow3r.core.pipeline.abc.pipeline_type import IPipelineType
from aaaflow3r.core.pipeline.pipeline_config import PipelineConfig
from aaaflow3r.core.placeholder.simple_placeholder_provider import SimplePlaceholderProvider
from aaaflow3r.core.source.abc.source import ISource
from aaaflow3r.core.source.abc.source_type import ISourceType
from aaaflow3r.core.source.source_config import SourceConfig
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


class ErrorSource(ISource):
    def __init__(self, exc: Exception):
        self._exc = exc
        self._stream = Stream(rx.throw(exc), rx.throw(exc))

    @property
    def stream(self) -> Stream:
        return self._stream

    def open(self):
        pass

    def close(self):
        pass


@dataclass
class Recording:
    start: Subject
    stop: Subject
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    primary_finished: bool = False
    secondary_finished: bool = False
    finished: bool = False
    progress: Tuple[int, int] = (0, 0)


@dataclass
class Session:
    group_id: str
    session_id: str
    recording_number: int
    recording: Optional[Recording] = None

    def get_placeholder_provider(self) -> SimplePlaceholderProvider:
        start_time = self.recording.start_time if self.recording and self.recording.start_time else datetime.now()
        return SimplePlaceholderProvider({
            "recording_number": self.recording_number,
            "start_time": start_time.strftime("%Y%m%d%H%M%S")
        })


@dataclass
class Group:
    group_id: str
    sessions: Dict[str, Session] = field(default_factory=dict)
    recording_number: int = 0
    active_session_id: Optional[str] = None
    pipeline: Optional[IPipeline] = None

    @property
    def active_session(self) -> Optional[Session]:
        return self.sessions.get(self.active_session_id)

    def new_session(self, active: bool = True):
        self.recording_number += 1
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(self.group_id, session_id, self.recording_number)
        if active:
            self.active_session_id = session_id
        return session_id


@dataclass(frozen=True)
class ChangeSet:
    # groups
    groups_added: List[GroupConfig]
    groups_removed: List[str]
    groups_updated: List[Tuple[GroupConfig, GroupConfig]]  # (old, new)

    # sources
    sources_added: List[SourceConfig]
    sources_removed: List[str]
    sources_updated: List[Tuple[SourceConfig, SourceConfig]]

    # pipelines
    pipelines_added: List[PipelineConfig]
    pipelines_removed: List[str]
    pipelines_updated: List[Tuple[PipelineConfig, PipelineConfig]]

    # derived / important semantic changes
    source_name_changed: List[Tuple[str, str]]  # source_id, new_name
    source_group_changed: List[Tuple[str, Optional[str], Optional[str]]]  # source_id, old_gid, new_gid

    group_name_changed: List[Tuple[str, str]]
    group_pipeline_changed: List[Tuple[str, Optional[str], Optional[str]]]  # group_id, old_pid, new_pid

    group_controls_changed: List[Tuple[str, str, Optional[str]]]  # group_id


def diff_by_id(old_map: Dict[str, Any], new_map: Dict[str, Any]):
    old_ids = set(old_map)
    new_ids = set(new_map)

    added_ids = new_ids - old_ids
    removed_ids = old_ids - new_ids
    kept_ids = old_ids & new_ids

    added = [new_map[_id] for _id in added_ids]
    removed = list(removed_ids)
    updated = [
        (old_map[_id], new_map[_id])
        for _id in kept_ids
        if old_map[_id] != new_map[_id]
    ]
    return added, removed, updated


def determine_location(sources: List[SourceConfig]) -> Tuple[str, Optional[str]]:
    if len(sources) == 0:
        return "hidden", None
    elif len(sources) == 1:
        return "source", sources[0].id
    else:
        return "bottom", None


def diff_config(old: AppConfig, new: AppConfig) -> ChangeSet:
    groups_added, groups_removed, groups_updated = diff_by_id(old.groups, new.groups)
    sources_added, sources_removed, sources_updated = diff_by_id(old.sources, new.sources)
    pipelines_added, pipelines_removed, pipelines_updated = diff_by_id(old.pipelines, new.pipelines)

    # semantic changes you care about (these drive runtime operations)
    source_name_changed: List[Tuple[str, str]] = []
    for old_sc, new_sc in sources_updated:
        if old_sc.name != new_sc.name:
            source_name_changed.append((new_sc.id, new_sc.name))

    source_group_changed: List[Tuple[str, Optional[str], Optional[str]]] = []
    for old_sc, new_sc in sources_updated:
        if old_sc.group_id != new_sc.group_id:
            source_group_changed.append((new_sc.id, old_sc.group_id, new_sc.group_id))

    group_name_changed: List[Tuple[str, str]] = []
    for old_gc, new_gc in groups_updated:
        if old_gc.name != new_gc.name:
            group_name_changed.append((new_gc.id, new_gc.name))

    group_pipeline_changed: List[Tuple[str, Optional[str], Optional[str]]] = []
    for old_gc, new_gc in groups_updated:
        if old_gc.pipeline_id != new_gc.pipeline_id:
            group_pipeline_changed.append((new_gc.id, old_gc.pipeline_id, new_gc.pipeline_id))

    group_controls_changed: List[Tuple[str, str, Optional[str]]] = []
    for gid, new_gc in new.groups.items():
        old_sources = [sc for sc in old.sources.values() if sc.group_id == gid]
        new_sources = [sc for sc in new.sources.values() if sc.group_id == gid]

        old_location, old_source_id = determine_location(old_sources)
        new_location, new_source_id = determine_location(new_sources)

        if gid in [g.id for g in groups_added] or old_location != new_location or old_source_id != new_source_id:
            group_controls_changed.append((gid, new_location, new_source_id))


    return ChangeSet(
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
        group_pipeline_changed=group_pipeline_changed,

        group_controls_changed=group_controls_changed
    )


class Controller(QObject):
    log_message = Signal(str)

    config_snapshot = Signal(AppConfig)
    config_changed = Signal(AppConfig)  # AppConfig

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
    progress_updated = Signal(str, str, Tuple[int, int])

    def __init__(self, source_types: Dict[str, ISourceType], pipeline_types: Dict[str, IPipelineType], widget_service: WidgetService):
        super().__init__()

        self.source_types = source_types
        self.pipeline_types = pipeline_types
        self.widget_service = widget_service

        self._config = AppConfig()
        self._draft: Optional[AppConfig] = None
        self._in_tx = 0

        self.sources: Dict[str, ISource] = {}
        self.source_widget_handles: Dict[str, IVisualizerHandle] = {}

        self.preview_scheduler = EventLoopScheduler()

        self.groups: Dict[str, Group] = {}

        self.primary_finished.connect(self._primary_finished)
        self.secondary_finished.connect(self._secondary_finished)
        self.progress_updated.connect(self._progress_updated)

    @property
    def config(self) -> AppConfig:
        return deepcopy(self._config)

    @contextmanager
    def transaction(self) -> Iterator[AppConfig]:
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
            yield self._draft
            # commit only at outermost
            self._commit(self._draft)
        finally:
            self._draft = None
            self._in_tx = 0

    def _commit(self, new_config: AppConfig):
        old_config = self._config
        changes = diff_config(old_config, new_config)

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

    def config_snapshot_requested(self):
        self.config_snapshot.emit(deepcopy(self.config))

    def send_source_snapshot(self, source_id: str):
        self.source_snapshot.emit(self.config.sources[source_id])

    def send_group_snapshot(self, group_id: str):
        self.group_snapshot.emit(self.config.groups[group_id])

    def send_active_session_snapshot(self, group_id: str):
        group = self.groups.get(group_id)
        if group and group.active_session_id:
            state = self._get_session_state(group_id, group.active_session_id)
            self.active_session_snapshot.emit(group_id, group.active_session_id, state)

    def add_source(self, source_config: SourceConfig):
        with self.transaction() as config:
            assert source_config.id not in config.sources

            config.sources[source_config.id] = source_config

            if not source_config.group_id:
                config.implicit_groups[source_config.id] = GroupConfig(source_config.id)
            else:
                config.implicit_groups.pop(source_config.id, None)

    def edit_source(self, source_config: SourceConfig):
        with self.transaction() as config:
            assert source_config.id in config.sources

            old_group_id = config.sources[source_config.id].group_id
            config.sources[source_config.id] = source_config

            if old_group_id != source_config.group_id:
                if source_config.group_id is None:
                    config.implicit_groups[source_config.id] = GroupConfig(source_config.id)
                else:
                    config.implicit_groups.pop(source_config.id, None)

    def remove_source(self, source_id: str):
        with self.transaction() as config:
            assert source_id in config.sources

            config.sources.pop(source_id, None)
            config.implicit_groups.pop(source_id, None)

    def setup_source(self, source_id: str):
        config = self.config
        assert source_id in config.sources

        self._stop_preview(source_id)
        self._teardown_source(source_id)

        source_config = config.sources[source_id]
        self._setup_source(source_config)
        self._start_preview(source_config)

    def add_group(self, group_config: GroupConfig):
        with self.transaction() as config:
           assert group_config.id not in config.groups

           config.groups[group_config.id] = group_config

    def edit_group(self, group_config: GroupConfig):
        with self.transaction() as config:
            assert group_config.id in config.groups

            config.groups[group_config.id] = group_config

    def remove_group(self, group_id: str):
        with self.transaction() as config:
            assert group_id in config.groups

            config.groups.pop(group_id, None)

    def assign_group(self, source_id: str, group_id: Optional[str]):
        with self.transaction() as config:
            print(config.sources)
            assert source_id in config.sources, f"SourceConfig {source_id} not found"
            assert group_id is None or group_id in config.groups, f"GroupConfig {group_id} not found"

            source_config = config.sources[source_id]
            source_config.group_id = group_id

            if not group_id:
                if source_id not in self.config.implicit_groups:
                    self.config.implicit_groups[source_id] = GroupConfig(source_id)
            else:
                self.config.implicit_groups.pop(source_id, None)

    def add_pipeline(self, pipeline_config: PipelineConfig):
        with self.transaction() as config:
            assert pipeline_config.id not in config.pipelines

            config.pipelines[pipeline_config.id] = pipeline_config

    def edit_pipeline(self, pipeline_config: PipelineConfig):
        with self.transaction() as config:
            assert pipeline_config.id in config.pipelines

            config.pipelines[pipeline_config.id] = pipeline_config

    def remove_pipeline(self, pipeline_id: str):
        with self.transaction() as config:
            assert pipeline_id in config.pipelines

            config.pipelines.pop(pipeline_id, None)

    def assign_pipeline(self, group_id: str, pipeline_id: Optional[str]):
        with self.transaction() as config:
            assert group_id in config.groups
            assert pipeline_id is None or pipeline_id in config.pipelines

            group_config = config.groups[group_id]
            group_config.pipeline_id = pipeline_id

    def _setup_pipeline(self, group_id: str, pipeline_config: Optional[PipelineConfig]):
        assert group_id in self.groups

        group = self.groups[group_id]

        if group.pipeline:
            group.pipeline.dispose()
            group.pipeline = None

        if pipeline_config:
            placeholder_provider = group.active_session.get_placeholder_provider()
            pipeline_type = self.pipeline_types.get(pipeline_config.pipeline_type)
            group.pipeline = pipeline_type.get_pipeline_factory()()
            app_context = AppContext(SessionWidgetServiceWrapper(self.widget_service, group_id, "preview"))
            group.pipeline.configure(app_context, pipeline_config.active_config.resolve(placeholder_provider))

    def start_recording(self, group_id: str, session_id: str):
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        assert group.pipeline is not None, f"Pipeline not set up for group {group_id}"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if session.recording:
            return

        from reactivex import operators as ops

        start = Subject()
        stop = Subject()
        session.recording = Recording(start, stop)

        source_configs = [sc for sc in self.config.sources.values() if sc.group_id == group_id]
        sources = [self.sources[sc.id] for sc in source_configs]
        source_descriptors = [s.stream.descriptor for s in sources]
        source_observables = [s.stream.observable.pipe(ops.publish()) for s in sources]
        source_streams = [Stream(desc, obs.pipe(ops.skip_until(start), ops.take_until(session.recording.stop))) for desc, obs in zip(source_descriptors, source_observables)]

        start_time = datetime.now()

        try:
            session.recording.start_time = start_time
            placeholder_provider = session.get_placeholder_provider()
            group_config = self.config.groups[group_id]
            pipeline_config = self.config.pipelines[group_config.pipeline_id]
            app_context = AppContext(SessionWidgetServiceWrapper(self.widget_service, group_id, session_id))
            group.pipeline.configure(app_context, pipeline_config.active_config.resolve(placeholder_provider))
            pipeline_sub = group.pipeline.build(app_context, source_streams)
        except:
            print(self.config)
            raise

        def _primary_done(fut: Future):
            exc = fut.exception()
            self.primary_finished.emit(group_id, session_id, exc)

        def _secondary_done(fut: Future):
            exc = fut.exception()
            self.secondary_finished.emit(group_id, session_id, exc)

        def _progress_updated(progress: Tuple[int, int]):
            self.progress_updated.emit(group_id, session_id, progress)

        pipeline_sub.primary_done.add_done_callback(_primary_done)
        pipeline_sub.secondary_done.add_done_callback(_secondary_done)
        if pipeline_sub.progress:
            pipeline_sub.progress.subscribe(_progress_updated)

        for obs in source_observables:
            obs.connect()

        session.recording.start.on_next(None)
        self._update_session_state(group_id, session_id)

    def stop_recording(self, group_id: str, session_id: str):
        print(f"stop_recording({group_id}, {session_id})")

        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if session.recording and not session.recording.stop_time:
            session.recording.stop_time = datetime.now()
            session.recording.stop.on_next(None)

        self._update_session_state(group_id, session_id)

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

    def _progress_updated(self, group_id: str, session_id: str, progress: Tuple[int, int]):
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if session.recording:
            session.recording.progress = progress

        self._update_session_state(group_id, session_id)

    def _recording_finished(self, group_id: str, session_id: str):
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        if not session.recording:
            return

        if session.recording.finished:
            return

        session.recording.finished = True

        group.new_session()
        self._update_active_session(group_id)
        self._update_session_state(group_id, session_id)

    def _apply_changes(self, changes: ChangeSet, old: AppConfig, new: AppConfig):
        sources_requiring_rebuild = [
            new_sc for old_sc, new_sc in changes.sources_updated
            if self._source_requires_rebuild(old_sc, new_sc)
        ]

        # --- 2) teardown removed sources/groups (sources first if they depend on groups) ---
        for sid in changes.sources_removed:
            self._stop_preview(sid)
            self._teardown_source(sid)

        for sc in sources_requiring_rebuild:
            self._stop_preview(sc.id)
            self._teardown_source(sc.id)

        for gid in changes.groups_removed:
            self._teardown_group(gid)

        # --- 3) create added groups/sources ---
        for gc in changes.groups_added:
            self._setup_group(new.groups[gc.id])

        for sc in changes.sources_added:
            self._setup_source(new.sources[sc.id])

        # --- 4) apply updates ---
        # pipelines: if a pipeline config changed, you might need to refresh all groups using it
        # You can precompute impacted groups.
        impacted_groups = {}

        for gc in changes.groups_added:
            impacted_groups[gc.id] = new.pipelines.get(gc.pipeline_id)

        for gid, old_pid, new_pid in changes.group_pipeline_changed:
            pipeline_config = new.pipelines[new_pid] if new_pid is not None else None
            impacted_groups[gid] = pipeline_config

        # If pipeline configs changed, re-setup groups that reference them.
        changed_pipeline_ids = {new_pc.id for (_, new_pc) in changes.pipelines_updated}
        removed_pipeline_ids = set(changes.pipelines_removed)
        if changed_pipeline_ids or removed_pipeline_ids:
            for gid, gc in new.groups.items():
                if gc.pipeline_id in changed_pipeline_ids or gc.pipeline_id in removed_pipeline_ids:
                    impacted_groups[gid] = new.pipelines.get(gc.pipeline_id)

        for gid, pipeline_config in impacted_groups.items():
            self._setup_pipeline(gid, pipeline_config)  # your existing method, but it should be idempotent

        # source edits may require teardown/setup; you can choose “patch” vs “rebuild”
        for sc in sources_requiring_rebuild:
            self._setup_source(sc)

        # --- 5) restart previews for relevant sources ---
        for sc in sources_requiring_rebuild:
            self._start_preview(sc)

        for sc in changes.sources_added:
            self._start_preview(sc)

        for gid, location, source_id in changes.group_controls_changed:
            self.widget_service.set_recording_controls_location(gid, location, source_id)

        # --- 6) ensure active sessions for groups that need it ---
        touched_groups = set(changes.groups_removed) | {gc.id for gc in changes.groups_added}
        touched_groups |= {gid for (gid, _, _) in changes.group_pipeline_changed}
        touched_groups |= {new_gid for (_, _, new_gid) in changes.source_group_changed if new_gid is not None}
        for gid in touched_groups:
            if gid in new.groups:
                self._ensure_active_session(gid)

    def _source_requires_rebuild(self, old_sc: SourceConfig, new_sc: SourceConfig) -> bool:
        return old_sc.active_config != new_sc.active_config

    def _setup_source(self, source_config: SourceConfig):
        print(f"_setup_source({source_config.id})")
        source_type = self.source_types.get(source_config.source_type)
        assert source_type is not None

        try:
            source_factory = source_type.get_source_factory()
            source = source_factory(source_config.active_config)
            print(f"Successfully set up source {source_config.id}:")
        except Exception as e:
            print(f"Error setting up source {source_config.id}: {e}")
            source = ErrorSource(e)

        self.sources[source_config.id] = source

        source.open()

    def _teardown_source(self, source_id: str):
        source = self.sources.pop(source_id, None)
        if source:
            source.close()

    def _setup_group(self, group_config: GroupConfig):
        if group_config.id not in self.groups:
            self.groups[group_config.id] = Group(group_config.id)
            print("Adding group controls:")
            self.widget_service.add_recording_controls(group_config.id)
            self.widget_service.set_recording_controls_location(group_config.id, "bottom")

    def _teardown_group(self, group_id: str):
        group = self.groups.pop(group_id, None)
        if group:
            self.widget_service.remove_recording_controls(group_id)
            if group.pipeline:
                group.pipeline.dispose()

    def _start_preview(self, source_config: SourceConfig):
        source_type = self.source_types.get(source_config.source_type)
        assert source_type is not None

        source = self.sources.get(source_config.id)
        assert source is not None

        source_widget_handle = self.widget_service.get_source_handle(source_config.id, "preview")
        self.source_widget_handles[source_config.id] = source_widget_handle

        source_widget_handle.subscribe(source.stream)

    def _stop_preview(self, source_id: str):
        source_widget_handle = self.source_widget_handles.pop(source_id, None)
        if source_widget_handle:
            source_widget_handle.unsubscribe()
            source_widget_handle.dispose()

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

        print(session)

        if session.recording:
            print("Has recording")
            if session.recording.start_time:
                print("Has start time")
                if session.recording.stop_time:
                    print("Has stop time")
                    if session.recording.primary_finished:
                        print("Has primary finished")
                        if session.recording.secondary_finished:
                            print("Has secondary finished")
                            return SessionState.Finished(start_time=session.recording.start_time, end_time=session.recording.stop_time)
                        else:
                            return SessionState.FinishingProcessing(start_time=session.recording.start_time, end_time=session.recording.stop_time)
                    else:
                        return SessionState.FinishingRecording(start_time=session.recording.start_time, end_time=session.recording.stop_time)
                else:
                    return SessionState.Running(start_time=session.recording.start_time)
            else:
                return SessionState.Ready()
        else:
            return SessionState.Ready()

    def _update_active_session(self, group_id: str):
        active_session_id = self.groups[group_id].active_session_id
        state = self._get_session_state(group_id, active_session_id)
        self.active_session_changed.emit(group_id, active_session_id, state)

    def _update_session_state(self, group_id: str, session_id: str):
        state = self._get_session_state(group_id, session_id)
        self.session_state_changed.emit(group_id, session_id, state)

    def _emit_entity_signals(self, changes: ChangeSet):
        for gc in changes.groups_added:
            self.group_added.emit(deepcopy(gc))
        for old_gc, new_gc in changes.groups_updated:
            self.group_changed.emit(deepcopy(new_gc))
        for gid in changes.groups_removed:
            self.group_removed.emit(gid)

        for sc in changes.sources_added:
            self.source_added.emit(deepcopy(sc))
        for old_sc, new_sc in changes.sources_updated:
            self.source_changed.emit(deepcopy(new_sc))
        for sid in changes.sources_removed:
            self.source_removed.emit(sid)

        for pc in changes.pipelines_added:
            self.pipeline_added.emit(deepcopy(pc))
        for old_pc, new_pc in changes.pipelines_updated:
            self.pipeline_changed.emit(deepcopy(new_pc))
        for pid in changes.pipelines_removed:
            self.pipeline_removed.emit(pid)
