import os
import uuid
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Iterator, List, Tuple, Any, Set

import yaml
from PySide6.QtCore import QObject, Signal, Slot, Qt
import reactivex as rx
from reactivex import Subject
from reactivex.abc import DisposableBase
from reactivex.scheduler import EventLoopScheduler

from flow3r.app.api.app.session_context import SessionContext
from flow3r.app.api.app.settings_view import SettingsView
from flow3r.app.api.plugins.plugins import PluginAPI
from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.group_config import GroupConfig
from flow3r.app.config.placeholder_config import PlaceholderConfig
from flow3r.app.controller.commit import ConfigChangeReply
from flow3r.app.controller.config_diff import ChangeSet, EffectSet, calculate_effects, diff_config
from flow3r.app.controller.placeholder_resolver import resolve_placeholders, UnknownPlaceholderError, CyclicPlaceholderError
from flow3r.app.controller.session_state import SessionStateBase, Finished, FinishingProcessing, FinishingRecording, Running, \
    Ready, NotReady, StartFailed, InvalidPlaceholders, CircularDependency
from flow3r.app.api.app.widget_service import WidgetService, SessionWidgetServiceWrapper
from flow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription, CompositePipelineSubscription, \
    PreviewSubscription, CompositePreviewSubscription
from flow3r.app.config.pipeline_config import PipelineConfig
from flow3r.core.placeholder.simple_placeholder_provider import SimplePlaceholderProvider
from flow3r.core.source.abc.source import ISource
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
    setup_error: Optional[str] = None
    preview_error: Optional[str] = None


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
    placeholder_recording_start_time: datetime = field(default_factory=datetime.now)
    recording: Optional[Recording] = None
    start_error: Optional[str] = None

    def get_placeholder_values(self) -> Dict[str, Any]:
        return {
            "group_name": self.group_name,
            "recording_number": str(self.recording_number),
            "recording_start_time": self.placeholder_recording_start_time.strftime("%Y%m%d%H%M%S")
        }


@dataclass
class Group:
    group_id: str
    group_name: str
    sessions: Dict[str, Session] = field(default_factory=dict)
    recording_number: int = 0
    recording_duration: Optional[float] = None
    active_session_id: Optional[str] = None
    source_ids: List[str] = field(default_factory=list)
    pipelines: Dict[str, IPipeline] = field(default_factory=dict)
    runtime_error: Optional[str] = None
    pipeline_errors: Dict[str, str] = field(default_factory=dict)
    preview_error: Optional[str] = None
    controls_initialized: bool = False
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


class Controller(QObject):
    log_message = Signal(str)

    settings_snapshot = Signal(object)  # settings state
    settings_changed = Signal(object)  # subset of state that changed

    config_snapshot = Signal(AppConfig)
    config_changed = Signal(AppConfig)  # AppConfig

    error = Signal(str, object)  # Exception

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

    placeholder_added = Signal(PlaceholderConfig)
    placeholder_changed = Signal(PlaceholderConfig)
    placeholder_removed = Signal(str)

    active_session_snapshot = Signal(str, str, SessionStateBase)  # group_id, session_id, state
    active_session_changed = Signal(str, str, SessionStateBase)  # group_id, session_id, state
    session_state_changed = Signal(str, str, SessionStateBase)  # group_id, session_id, state

    primary_finished = Signal(str, str, object)  # group_id, session_id, exc
    secondary_finished = Signal(str, str, object)  # group_id, session_id, exc
    progress_updated = Signal(str, str, object)  # group_id, session_id, progress

    config_loaded = Signal(object)  # window layout

    def __init__(self, plugin_api: PluginAPI, widget_service: WidgetService):
        super().__init__()

        self.config_types = plugin_api.config_types.config_types
        self.source_types = plugin_api.source_types.get_source_types()
        self.pipeline_types = plugin_api.pipeline_types.get_pipeline_types()
        self.widget_service = widget_service

        self._config = AppConfig()
        self._draft: Optional[AppConfig] = None
        self._applying_config: Optional[AppConfig] = None
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

    @property
    def _effective_config(self) -> AppConfig:
        if self._applying_config is not None:
            return self._applying_config
        return self._config

    @staticmethod
    def _session_has_started(session: Session) -> bool:
        return session.recording is not None and session.recording.start_time is not None

    @staticmethod
    def _format_exception(exc: BaseException) -> str:
        message = str(exc).strip()
        return message or exc.__class__.__name__

    def _set_source_setup_error(self, source_id: str, error: Optional[str]):
        source_entry = self.sources.get(source_id)
        if source_entry is not None:
            source_entry.setup_error = error

    def _set_source_preview_error(self, source_id: str, error: Optional[str]):
        source_entry = self.sources.get(source_id)
        if source_entry is not None:
            source_entry.preview_error = error

    def _set_group_runtime_error(self, group_id: str, error: Optional[str]):
        group = self.groups.get(group_id)
        if group is not None:
            group.runtime_error = error

    def _set_group_preview_error(self, group_id: str, error: Optional[str]):
        group = self.groups.get(group_id)
        if group is not None:
            group.preview_error = error

    def _set_session_start_error(self, group_id: str, session_id: str, error: Optional[str]):
        group = self.groups.get(group_id)
        if group is None:
            return

        session = group.sessions.get(session_id)
        if session is not None:
            session.start_error = error

    def _refresh_group_runtime_snapshot(self, group_id: str, config: Optional[AppConfig] = None):
        config = config or self._effective_config
        group = self.groups.get(group_id)
        group_config = config.all_groups.get(group_id)
        if group is None or group_config is None:
            return

        recording_duration = group_config.recording_config.recording_duration if group_config.recording_config.recording_mode == "timed" else None
        group.group_name = group_config.name
        group.recording_duration = recording_duration
        group.source_ids = [
            source_config.id
            for source_config in config.sources.values()
            if source_config.implicit_group_id == group_id
        ]

    def _refresh_group_state(self, group_id: str):
        import traceback

        group = self.groups.get(group_id)
        if group is None:
            return

        try:
            self._update_active_session(group_id)
        except Exception:
            traceback.print_exc()

        for session_id in list(group.sessions):
            try:
                self._update_session_state(group_id, session_id)
            except Exception:
                traceback.print_exc()

    def _refresh_all_group_states(self):
        for group_id in list(self.groups):
            self._refresh_group_state(group_id)

    def _record_unhandled_apply_error(self, effects: EffectSet, exc: Exception):
        message = f"Unexpected runtime reconciliation error: {self._format_exception(exc)}"

        for group_id in effects.impacted_group_ids:
            self._set_group_runtime_error(group_id, message)

    def _refresh_mutable_session_group_names(self, group_id: str, group_name: str) -> Set[Tuple[str, str]]:
        group = self.groups[group_id]
        updated_sessions: Set[Tuple[str, str]] = set()

        for session in group.sessions.values():
            if self._session_has_started(session) or session.group_name == group_name:
                continue

            session.group_name = group_name
            updated_sessions.add((group_id, session.session_id))

        return updated_sessions

    def _refresh_mutable_session_recording_durations(self, group_id: str, recording_duration: Optional[float]) -> Set[Tuple[str, str]]:
        group = self.groups[group_id]
        updated_sessions: Set[Tuple[str, str]] = set()

        for session in group.sessions.values():
            if self._session_has_started(session) or session.recording_duration == recording_duration:
                continue

            session.recording_duration = recording_duration
            updated_sessions.add((group_id, session.session_id))

        return updated_sessions

    def _mutable_session_ids(self, group_id: str) -> Set[Tuple[str, str]]:
        group = self.groups[group_id]
        return {
            (group_id, session.session_id)
            for session in group.sessions.values()
            if not self._session_has_started(session)
        }

    def _recording_group_ids(self) -> Set[str]:
        recording_group_ids = set()
        for group_id, group in self.groups.items():
            active_session = group.active_session
            if active_session is not None and self._session_has_started(active_session):
                recording_group_ids.add(group_id)
        return recording_group_ids

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
            import traceback
            traceback.print_exc()
            self.error.emit("Config change failed", exc)
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
        effects = calculate_effects(changes, old_config, new_config, self._recording_group_ids())

        self._check_permission(changes)

        self._config = new_config
        self._applying_config = new_config
        for group_id in effects.impacted_group_ids:
            self._set_group_runtime_error(group_id, None)

        try:
            try:
                self._apply_changes(changes, effects, old_config, new_config)
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self._record_unhandled_apply_error(effects, exc)
        finally:
            self._applying_config = None
            # Emit signals after the runtime reconciliation attempt so listeners
            # observe the committed config together with the final runtime state.
            self.config_changed.emit(deepcopy(self._config))
            self._emit_entity_signals(changes)
            self._refresh_all_group_states()

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

    def _reconcile_runtime_with_committed_config(self):
        config = self._config

        for source_id in list(self.sources):
            if source_id in config.sources:
                continue
            try:
                self._stop_preview(source_id)
                self._teardown_source(source_id)
                self._teardown_source_widget(source_id)
            except Exception:
                import traceback
                traceback.print_exc()

        for group_id in list(self.groups):
            if group_id in config.all_groups:
                continue
            try:
                self._stop_pipeline_preview(group_id)
                self._teardown_group(group_id)
            except Exception:
                import traceback
                traceback.print_exc()

        for group_id, group_config in config.all_groups.items():
            try:
                self._setup_group(group_config)
                self._refresh_group_runtime_snapshot(group_id, config)
                self._ensure_active_session(group_id)
            except Exception as exc:
                self._set_group_runtime_error(group_id, f"Unexpected runtime reconciliation error: {self._format_exception(exc)}")

        for source_config in config.sources.values():
            try:
                self._setup_source_widget(source_config)
                self._setup_source(source_config)
                self._start_preview(source_config)
            except Exception as exc:
                message = self._format_exception(exc)
                self._set_source_setup_error(source_config.id, message)
                self._set_source_preview_error(source_config.id, message)

        for group_id, group_config in config.all_groups.items():
            group = self.groups.get(group_id)
            if group is None:
                continue

            desired_pipeline_ids = set(group_config.pipeline_ids)
            for pipeline_id in list(group.pipelines):
                if pipeline_id in desired_pipeline_ids:
                    continue
                try:
                    self._teardown_pipeline(group_id, pipeline_id)
                except Exception:
                    import traceback
                    traceback.print_exc()

            for pipeline_id in desired_pipeline_ids:
                try:
                    self._setup_pipeline(group_id, pipeline_id)
                except Exception as exc:
                    group.pipeline_errors[pipeline_id] = self._format_exception(exc)

            active_session = group.active_session
            if active_session is None or not self._session_has_started(active_session):
                self._start_pipeline_preview(group_id)

        self._refresh_all_group_states()

    @Slot()
    def reconcile_runtime(self):
        self._reconcile_runtime_with_committed_config()

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

        self._start_pipeline_preview(source_config.implicit_group_id)
        self._refresh_group_state(source_config.implicit_group_id)

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

    @Slot(object)
    def add_placeholder(self, placeholder_config: PlaceholderConfig):
        with self.transaction() as config:
            assert placeholder_config.id not in config.placeholders
            config.placeholders[placeholder_config.id] = placeholder_config

    @Slot(object)
    def edit_placeholder(self, placeholder_config: PlaceholderConfig):
        with self.transaction() as config:
            assert placeholder_config.id in config.placeholders
            config.placeholders[placeholder_config.id] = placeholder_config

    @Slot(str)
    def remove_placeholder(self, placeholder_id: str):
        with self.transaction() as config:
            assert placeholder_id in config.placeholders
            config.placeholders.pop(placeholder_id, None)

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

    @Slot(object)
    def update_global_placeholder_values(self, changed_values: Dict[str, str]):
        with self.transaction() as config:
            for placeholder_id, value in changed_values.items():
                config.global_placeholder_values[placeholder_id] = value

    def _dispose_recording_resources(self, recording: Optional[Recording]):
        if recording is None:
            return

        if recording.pipeline_sub is not None:
            try:
                recording.pipeline_sub.dispose()
            except Exception:
                import traceback
                traceback.print_exc()

        for connection in recording.connections or []:
            try:
                connection.dispose()
            except Exception:
                import traceback
                traceback.print_exc()

    def _fail_recording_start(
        self,
        group_id: str,
        session_id: str,
        error: str,
        *,
        recording: Optional[Recording] = None,
        restart_preview: bool = False,
    ):
        if recording is not None:
            self._dispose_recording_resources(recording)

        self._set_session_start_error(group_id, session_id, error)
        if restart_preview:
            self._start_pipeline_preview(group_id)
        self._refresh_group_state(group_id)

    @Slot(str, str)
    def start_recording(self, group_id: str, session_id: str):
        print(f"start_recording({group_id}, {session_id})")
        group = self.groups.get(group_id)
        if group is None:
            return

        session = group.sessions.get(session_id)
        if session is None:
            return

        if session.recording and session.recording.start_time:
            return

        self._set_session_start_error(group_id, session_id, None)

        config = self._effective_config
        group_config = config.all_groups.get(group_id)
        if group_config is None:
            self._fail_recording_start(group_id, session_id, f"Group '{group_id}' is not configured")
            return

        if group.runtime_error:
            self._refresh_group_state(group_id)
            return

        if group.pipeline_errors:
            self._refresh_group_state(group_id)
            return

        pipeline_configs = [config.pipelines[pipeline_id] for pipeline_id in group_config.pipeline_ids if pipeline_id in config.pipelines]
        if not pipeline_configs:
            self._fail_recording_start(group_id, session_id, "No pipelines configured")
            return

        missing_pipeline_ids = [pipeline_config.id for pipeline_config in pipeline_configs if pipeline_config.id not in group.pipelines]
        if missing_pipeline_ids:
            self._fail_recording_start(group_id, session_id, f"Pipelines are not set up: {', '.join(missing_pipeline_ids)}")
            return

        source_configs = [sc for sc in config.sources.values() if sc.implicit_group_id == group_id]
        recording = Recording(Subject(), Subject())

        from reactivex import operators as ops

        source_observables = []
        source_streams: Dict[str, Dict[str, Stream]] = {}

        try:
            for pipeline_config in pipeline_configs:
                if pipeline_config.id not in source_streams:
                    source_streams[pipeline_config.id] = {}

                if len(pipeline_config.active_config.inputs) == len(source_configs) == 1:
                    input_name = pipeline_config.active_config.inputs[0]
                    source_config = source_configs[0]
                    source_entry = self.sources.get(source_config.id)
                    if source_entry is None or source_entry.source is None:
                        raise Exception(f"Source '{source_config.id}' is not available")
                    if source_entry.setup_error:
                        raise Exception(f"Source '{source_entry.name}' is not ready: {source_entry.setup_error}")

                    format = source_entry.source.stream.format
                    observable = source_entry.source.stream.data.pipe(ops.publish())
                    source_observables.append(observable)
                    gated_observable = observable.pipe(ops.skip_until(recording.start), ops.take_until(recording.stop))
                    source_streams[pipeline_config.id][input_name] = Stream(format, gated_observable, name=source_entry.name)
                else:
                    mapping = group_config.source_mapping.get(pipeline_config.id, {})
                    for input_name in pipeline_config.active_config.inputs:
                        source_id = mapping.get(input_name)
                        if source_id is None:
                            raise Exception(f"Pipeline '{pipeline_config.name}' is missing a source assignment for input '{input_name}'")

                        source_entry = self.sources.get(source_id)
                        if source_entry is None or source_entry.source is None:
                            raise Exception(f"Source '{source_id}' is not available")
                        if source_entry.setup_error:
                            raise Exception(f"Source '{source_entry.name}' is not ready: {source_entry.setup_error}")

                        format = source_entry.source.stream.format
                        observable = source_entry.source.stream.data.pipe(ops.publish())
                        source_observables.append(observable)
                        gated_observable = observable.pipe(ops.skip_until(recording.start), ops.take_until(recording.stop))
                        source_streams[pipeline_config.id][input_name] = Stream(format, gated_observable, name=source_entry.name)
        except Exception as exc:
            self._fail_recording_start(group_id, session_id, self._format_exception(exc))
            return

        preview_was_running = group.preview is not None
        if preview_was_running:
            self._stop_pipeline_preview(group_id)

        try:
            global_placeholder_values = config.global_placeholder_values_dict
            session_placeholder_values = session.get_placeholder_values()
            placeholder_values = resolve_placeholders(global_placeholder_values | session_placeholder_values)
            placeholder_provider = SimplePlaceholderProvider(placeholder_values)

            widget_service = SessionWidgetServiceWrapper(self.widget_service, group_id, session_id)
            settings_view = SettingsView(config.settings)
            session_context = SessionContext(widget_service, settings_view)

            pipeline_subs = []
            for pipeline_config in pipeline_configs:
                resolved_config = pipeline_config.active_config.resolve(placeholder_provider)
                pipeline = group.pipelines[pipeline_config.id]
                try:
                    pipeline.configure(session_context, resolved_config)
                    sub = pipeline.build(session_context, source_streams[pipeline_config.id])
                    if sub is None:
                        raise Exception(f"Pipeline '{pipeline_config.name}' did not create a recording subscription")
                    pipeline_subs.append(sub)
                except Exception:
                    for pipeline_sub in pipeline_subs:
                        try:
                            pipeline_sub.dispose()
                        except Exception:
                            import traceback
                            traceback.print_exc()
                    raise

            recording.pipeline_sub = CompositePipelineSubscription(pipeline_subs)
            recording.start_time = datetime.now()
            recording.connections = []

            for obs in source_observables:
                sub = obs.connect()
                recording.connections.append(sub)

            session.recording = recording
            recording.start.on_next(None)

        except Exception as exc:
            self._fail_recording_start(
                group_id,
                session_id,
                self._format_exception(exc),
                recording=recording,
                restart_preview=preview_was_running,
            )
            return

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

        assert session.recording is not None and session.recording.pipeline_sub is not None
        session.recording.pipeline_sub.primary_done.pipe(ops.take(1)).subscribe(_primary_done, _primary_failed)
        session.recording.pipeline_sub.secondary_done.pipe(ops.take(1)).subscribe(_secondary_done, _secondary_failed)
        if session.recording.pipeline_sub.progress:
            session.recording.pipeline_sub.progress.subscribe(_progress_updated)

        self._refresh_group_state(group_id)

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

        if session.recording.stop_time is None:
            session.recording.stop_time = datetime.now()

        session.recording.finished = True

        self._dispose_recording_resources(session.recording)

        new_session_id = group.new_session()
        self._refresh_group_runtime_snapshot(group_id)
        self._update_active_session(group_id)
        self._update_session_state(group_id, session_id)

        self._start_pipeline_preview(group_id)
        self._refresh_group_state(group_id)

    def _pipeline_input_mapping(self, group_id: str, pipeline_id: str) -> Dict[str, str]:
        config = self._effective_config
        group_config = config.all_groups[group_id]
        pipeline_config = config.pipelines[pipeline_id]

        source_configs = [sc for sc in config.sources.values() if sc.implicit_group_id == group_id]

        if len(pipeline_config.active_config.inputs) == len(source_configs) == 1:
            input_name = pipeline_config.active_config.inputs[0]
            source_config = source_configs[0]
            return {input_name: source_config.id}
        else:
            return group_config.source_mapping.get(pipeline_config.id, {})

    def _start_pipeline_preview(self, group_id: str):
        group = self.groups.get(group_id)
        if group is None:
            return

        self._set_group_preview_error(group_id, None)

        config = self._effective_config
        group_config = config.all_groups.get(group_id)
        if group_config is None:
            return

        source_configs = [sc for sc in config.sources.values() if sc.implicit_group_id == group_id]

        if not len(group_config.pipeline_ids) > 0:
            return

        pipeline_configs = [config.pipelines[pipeline_id] for pipeline_id in group_config.pipeline_ids if pipeline_id in config.pipelines]
        if len(pipeline_configs) != len(group_config.pipeline_ids):
            missing_pipeline_ids = [pipeline_id for pipeline_id in group_config.pipeline_ids if pipeline_id not in config.pipelines]
            self._set_group_preview_error(group_id, f"Pipelines are not configured: {', '.join(missing_pipeline_ids)}")
            return

        if group.preview:
            return

        for pipeline_config in pipeline_configs:
            self._configure_pipeline(group_id, pipeline_config.id)

        blocking_pipeline_errors = {
            pipeline_id: error_message
            for pipeline_id, error_message in group.pipeline_errors.items()
            if pipeline_id in group_config.pipeline_ids
        }
        if blocking_pipeline_errors:
            pipeline_id, error_message = next(iter(blocking_pipeline_errors.items()))
            pipeline_name = config.pipelines[pipeline_id].name if pipeline_id in config.pipelines else pipeline_id
            self._set_group_preview_error(group_id, f"Pipeline '{pipeline_name}' is not ready: {error_message}")
            return

        missing_pipeline_ids = [pipeline_config.id for pipeline_config in pipeline_configs if pipeline_config.id not in group.pipelines]
        if missing_pipeline_ids:
            self._set_group_preview_error(group_id, f"Pipelines are not set up: {', '.join(missing_pipeline_ids)}")
            return

        if not all(
            len(pc.active_config.inputs) == len(source_configs) == 1 or \
            all(input_name in group_config.source_mapping[pc.id] for input_name in pc.active_config.inputs)
            for pc in pipeline_configs
        ):
            self._set_group_preview_error(group_id, "Preview input mapping is incomplete")
            return

        from reactivex import operators as ops

        source_observables = []

        source_streams: Dict[str, Dict[str, IStream]] = {}
        try:
            for pipeline_config in pipeline_configs:
                if pipeline_config.id not in source_streams:
                    source_streams[pipeline_config.id] = {}

                input_mapping = self._pipeline_input_mapping(group_id, pipeline_config.id)

                for input_name in pipeline_config.active_config.inputs:
                    source_id = input_mapping.get(input_name)
                    if source_id is None:
                        raise Exception(f"Pipeline '{pipeline_config.name}' is missing a source assignment for input '{input_name}'")

                    source_entry = self.sources.get(source_id)
                    if source_entry is None or source_entry.source is None:
                        raise Exception(f"Source '{source_id}' is not available")
                    if source_entry.setup_error:
                        raise Exception(f"Source '{source_entry.name}' is not ready: {source_entry.setup_error}")

                    format = source_entry.source.stream.format
                    observable = source_entry.source.stream.data.pipe(ops.publish())
                    source_observables.append(observable)
                    source_streams[pipeline_config.id][input_name] = Stream(format, observable, source_entry.name)
        except Exception as exc:
            self._set_group_preview_error(group_id, self._format_exception(exc))
            return

        try:
            widget_service = SessionWidgetServiceWrapper(self.widget_service, group_id, "preview")
            settings_view = SettingsView(config.settings)
            session_context = SessionContext(widget_service, settings_view)

            preview_subs = []
            for pipeline_config in pipeline_configs:
                pipeline = group.pipelines[pipeline_config.id]
                try:
                    sub = pipeline.preview(session_context, source_streams[pipeline_config.id])
                    if sub is None:
                        raise Exception(f"Pipeline '{pipeline_config.name}' did not create a preview")
                except Exception as exc:
                    for preview_sub in preview_subs:
                        try:
                            preview_sub.dispose()
                        except Exception:
                            import traceback
                            traceback.print_exc()
                    raise Exception(f"Pipeline '{pipeline_config.name}' preview failed: {self._format_exception(exc)}") from exc

                preview_subs.append(sub)

            preview_sub = CompositePreviewSubscription(preview_subs)

        except Exception as exc:
            self._set_group_preview_error(group_id, self._format_exception(exc))
            return

        def _preview_done(_):
            print("Preview done")

        def _preview_failed(exc: Exception):
            print(f"Preview primary failed: {exc}")
            self._stop_pipeline_preview(group_id)
            self._set_group_preview_error(group_id, self._format_exception(exc))
            self._refresh_group_state(group_id)

        preview_sub.done.pipe(ops.take(1)).subscribe(_preview_done, _preview_failed)

        connections = []
        for obs in source_observables:
            sub = obs.connect()
            connections.append(sub)

        group.preview = Preview(connections, preview_sub)

    def _stop_pipeline_preview(self, group_id: str):
        group = self.groups.get(group_id)
        if group is None:
            return

        preview = group.preview

        if preview is None:
            return

        if preview.preview_sub is not None:
            try:
                preview.preview_sub.dispose()
                print("Disposed preview subscription")
            except Exception:
                import traceback
                traceback.print_exc()
        for connection in preview.connections:
            try:
                connection.dispose()
            except Exception:
                import traceback
                traceback.print_exc()
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
        changed_sources = [source_config for source_config, _ in changes.sources_updated.values()]
        changed_sources += [source_config for source_config in changes.sources_removed.values()]
        for source_config in changed_sources:
            group = self.groups.get(source_config.implicit_group_id)
            if group is not None and any(session.recording and session.recording.start_time and not session.recording.finished for session in group.sessions.values()):
                raise Exception("Cannot edit source while it is used in a recording")

    def _apply_changes(self, changes: ChangeSet, effects: EffectSet, old: AppConfig, new: AppConfig):
        for group_id in effects.groups_requiring_preview_stop:
            print(f"Stopping preview for group {group_id}")
            self._stop_pipeline_preview(group_id)

        # --- 2) teardown removed sources/groups (sources first if they depend on groups) ---
        for source_id in effects.source_previews_to_stop:
            self._stop_preview(source_id)

        for sid in changes.sources_removed:
            self._teardown_source(sid)
            self._teardown_source_widget(sid)

        for source_id in effects.sources_requiring_rebuild:
            self._teardown_source(source_id)

        for gid in changes.groups_removed:
            self._teardown_group(gid)

        # --- 3) create added groups/sources ---
        for group_config in changes.groups_added.values():
            self._setup_group(group_config)

        for source_config in changes.sources_added.values():
            self._setup_source_widget(source_config)
            self._setup_source(source_config)

        for group_id in new.all_groups:
            self._refresh_group_runtime_snapshot(group_id, new)

        for group_config in new.all_groups.values():
            self._ensure_active_session(group_config.id)

        sessions_to_update = set()
        for group_id, group_name in changes.group_name_changed:
            group = self.groups[group_id]
            group.group_name = group_name
            sessions_to_update.update(self._refresh_mutable_session_group_names(group_id, group_name))

        for group_id, (_old_duration, new_duration) in changes.group_recording_duration_changed.items():
            group = self.groups[group_id]
            group.recording_duration = new_duration
            sessions_to_update.update(self._refresh_mutable_session_recording_durations(group_id, new_duration))

        for group_id in effects.groups_requiring_session_state_refresh:
            if group_id in self.groups:
                sessions_to_update.update(self._mutable_session_ids(group_id))

        # --- 4) apply updates ---
        for group_id in changes.groups_added:
            for pipeline_id in new.all_groups[group_id].pipeline_ids:
                self._setup_pipeline(group_id, pipeline_id)

        for group_id, pipeline_id in changes.group_pipeline_updated:
            group = self.groups[group_id]
            active_session = group.active_session
            if active_session is not None and not self._session_has_started(active_session):
                sessions_to_update.add((group_id, group.active_session_id))

            old_pipeline_config, new_pipeline_config = old.pipelines[pipeline_id], new.pipelines[pipeline_id]
            if old_pipeline_config.pipeline_type == new_pipeline_config.pipeline_type:
                self._configure_pipeline(group_id, pipeline_id)
            else:
                self._teardown_pipeline(group_id, pipeline_id)
                self._setup_pipeline(group_id, pipeline_id)

        for group_id, pipeline_id in changes.group_pipeline_added:
            self._setup_pipeline(group_id, pipeline_id)

        for group_id, pipeline_id in changes.group_pipeline_removed:
            self._teardown_pipeline(group_id, pipeline_id)

        for sc in effects.sources_requiring_rebuild.values():
            self._setup_source(sc)

        # --- 5) restart previews for relevant sources ---
        for sc in effects.source_previews_to_start.values():
            self._start_preview(sc)

        for group_id in effects.groups_requiring_preview_start:
            self._start_pipeline_preview(group_id)

        for gid, location, source_id in effects.group_controls_changed:
            try:
                self.widget_service.set_recording_controls_location(gid, location, source_id)
            except Exception as exc:
                self._set_group_runtime_error(gid, self._format_exception(exc))

        for group_id, session_id in sessions_to_update:
            self._update_session_state(group_id, session_id)

    def _setup_source_widget(self, source_config: SourceConfig):
        if source_config.id not in self.sources:
            self.sources[source_config.id] = SourceEntry()

        source_entry = self.sources[source_config.id]

        if not source_entry.widget_handle:
            try:
                source_entry.widget_handle = self.widget_service.get_source_handle(source_config.id, "preview")
                self._set_source_preview_error(source_config.id, None)
            except Exception as exc:
                self._set_source_preview_error(source_config.id, self._format_exception(exc))

    def _teardown_source_widget(self, source_id: str):
        source_entry = self.sources.pop(source_id, None)
        if not source_entry or not source_entry.widget_handle:
            return
        try:
            source_entry.widget_handle.dispose()
        except Exception:
            import traceback
            traceback.print_exc()
        source_entry.widget_handle = None

    def _setup_source(self, source_config: SourceConfig):
        if source_config.id not in self.sources:
            self.sources[source_config.id] = SourceEntry()

        source_entry = self.sources[source_config.id]
        source_entry.name = source_config.name

        source_type = self.source_types.get(source_config.source_type)
        assert source_type is not None

        self._set_source_setup_error(source_config.id, None)

        source = None
        try:
            source_factory = source_type.source_factory
            source = source_factory(source_config.active_config)
            source.open()
        except Exception as exc:
            if source is not None:
                try:
                    source.close()
                except Exception:
                    import traceback
                    traceback.print_exc()
            source = ErrorSource(exc)
            self._set_source_setup_error(source_config.id, self._format_exception(exc))
            try:
                source.open()
            except Exception:
                pass

        source_entry.source = source

    def _teardown_source(self, source_id: str):
        print(f"_teardown_source({source_id})")
        source_entry = self.sources.get(source_id, None)
        if not source_entry or not source_entry.source:
            return

        try:
            source_entry.source.close()
        except Exception:
            import traceback
            traceback.print_exc()
        source_entry.source = None

    def _setup_group(self, group_config: GroupConfig):
        if group_config.id not in self.groups:
            recording_duration = group_config.recording_config.recording_duration if group_config.recording_config.recording_mode == "timed" else None
            self.groups[group_config.id] = Group(group_config.id, group_config.name, recording_duration=recording_duration)
        group = self.groups[group_config.id]
        group.group_name = group_config.name
        self._set_group_runtime_error(group_config.id, None)
        self._refresh_group_runtime_snapshot(group_config.id)

        try:
            if not group.controls_initialized:
                print("Adding group controls:")
                self.widget_service.add_recording_controls(group_config.id)
                group.controls_initialized = True
            self.widget_service.set_recording_controls_location(group_config.id, "bottom")
        except Exception as exc:
            self._set_group_runtime_error(group_config.id, self._format_exception(exc))

    def _teardown_group(self, group_id: str):
        group = self.groups.pop(group_id, None)
        if group:
            try:
                self.widget_service.remove_recording_controls(group_id)
            except Exception:
                import traceback
                traceback.print_exc()
            for pipeline in group.pipelines.values():
                try:
                    pipeline.dispose()
                except Exception:
                    import traceback
                    traceback.print_exc()

    def _start_preview(self, source_config: SourceConfig):
        source_entry = self.sources.get(source_config.id)
        if source_entry is None:
            return
        if source_entry.source is None:
            self._set_source_preview_error(source_config.id, "Source is not available")
            return
        if source_entry.widget_handle is None:
            self._set_source_preview_error(source_config.id, "Preview widget is not available")
            return
        if source_entry.preview_sub is not None:
            return

        widget_handle = source_entry.widget_handle

        self._set_source_preview_error(source_config.id, None)

        try:
            widget_handle.set_error(None)
            widget_handle.set_format(source_entry.source.stream.format)

            def _on_preview_error(exc: Exception):
                source_entry.preview_sub = None
                if source_entry.setup_error is None:
                    self._set_source_preview_error(source_config.id, self._format_exception(exc))
                widget_handle.set_error(exc)
                self._refresh_group_state(source_config.implicit_group_id)

            source_entry.preview_sub = source_entry.source.stream.data.subscribe(
                on_next=widget_handle.set_item,
                on_error=_on_preview_error,
                on_completed=lambda: widget_handle.set_completed(True)
            )
        except Exception as exc:
            self._set_source_preview_error(source_config.id, self._format_exception(exc))
            try:
                widget_handle.set_error(exc)
            except Exception:
                import traceback
                traceback.print_exc()

    def _stop_preview(self, source_id: str):
        print(f"_stop_preview({source_id})")
        source_entry = self.sources.get(source_id)

        if not source_entry:
            return

        if source_entry.preview_sub:
            print("Unsubscribing from source preview")
            try:
                source_entry.preview_sub.dispose()
            except Exception:
                import traceback
                traceback.print_exc()
            source_entry.preview_sub = None

    def _setup_pipeline(self, group_id: str, pipeline_id: str):
        config = self._effective_config
        assert pipeline_id in config.pipelines
        pipeline_config = config.pipelines[pipeline_id]

        assert group_id in self.groups
        group = self.groups[group_id]

        pipeline = group.pipelines.get(pipeline_config.id)
        if pipeline is not None:
            return

        try:
            pipeline_type = self.pipeline_types.get(pipeline_config.pipeline_type)
            assert pipeline_type is not None
            pipeline_factory = pipeline_type.pipeline_factory
            pipeline = pipeline_factory()
        except Exception as exc:
            group.pipeline_errors[pipeline_config.id] = self._format_exception(exc)
            return

        group.pipelines[pipeline_config.id] = pipeline

        self._configure_pipeline(group_id, pipeline_id)

    def _configure_pipeline(self, group_id: str, pipeline_id: str):
        config = self._effective_config
        if pipeline_id not in config.pipelines:
            return
        pipeline_config = config.pipelines[pipeline_id]

        assert group_id in self.groups
        group = self.groups[group_id]

        pipeline = group.pipelines.get(pipeline_config.id)
        if pipeline is None:
            group.pipeline_errors[pipeline_config.id] = "Pipeline is not set up"
            return

        active_session = group.active_session
        if active_session is None:
            group.pipeline_errors[pipeline_config.id] = "No active session available"
            return

        try:
            global_placeholder_values = config.global_placeholder_values_dict
            session_placeholder_values = active_session.get_placeholder_values()
            placeholder_values = resolve_placeholders(global_placeholder_values | session_placeholder_values)
            placeholder_provider = SimplePlaceholderProvider(placeholder_values)

            widget_service = SessionWidgetServiceWrapper(self.widget_service, group_id, "preview")
            settings_view = SettingsView(config.settings)
            session_context = SessionContext(widget_service, settings_view)

            input_mapping = self._pipeline_input_mapping(group_id, pipeline_config.id)
            for input_name in pipeline_config.active_config.inputs:
                if input_name not in input_mapping:
                    raise Exception(f"Missing source assignment for input '{input_name}'")

            pipeline.configure(session_context, pipeline_config.active_config.resolve(placeholder_provider))
        except Exception as exc:
            group.pipeline_errors[pipeline_config.id] = self._format_exception(exc)
            return

        group.pipeline_errors.pop(pipeline_config.id, None)

    def _teardown_pipeline(self, group_id: str, pipeline_id: str):
        group = self.groups[group_id]
        group.pipeline_errors.pop(pipeline_id, None)
        pipeline = group.pipelines.pop(pipeline_id, None)
        if pipeline:
            try:
                pipeline.dispose()
            except Exception:
                import traceback
                traceback.print_exc()

    def _ensure_active_session(self, group_id: str):
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"
        if group.active_session_id is None:
            session_id = group.new_session()
            self._refresh_group_runtime_snapshot(group_id)
            self._update_active_session(group_id)

    def _get_session_state(self, group_id: str, session_id: str):
        config = self._effective_config

        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"

        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found for group {group_id}"

        duration = session.recording_duration

        if session.recording and session.recording.start_time:
            start_time = session.recording.start_time
            stop_time = session.recording.stop_time

            if stop_time:
                if session.recording.primary_finished:
                    if session.recording.secondary_finished:
                        return Finished(recording_number=session.recording_number, start_time=start_time, stop_time=stop_time, end_time=stop_time, duration=duration)
                    return FinishingProcessing(recording_number=session.recording_number, start_time=start_time, stop_time=stop_time, duration=duration)
                return FinishingRecording(recording_number=session.recording_number, start_time=start_time, stop_time=stop_time, duration=duration)

            return Running(recording_number=session.recording_number, start_time=start_time, duration=duration)

        if group.runtime_error:
            return NotReady(
                recording_number=session.recording_number,
                duration=duration,
                reason=f"Group '{group.group_name}' is not ready: {group.runtime_error}",
            )

        for source_id in group.source_ids:
            source_entry = self.sources.get(source_id)
            if source_entry is None:
                return NotReady(
                    recording_number=session.recording_number,
                    duration=duration,
                    reason=f"Source '{source_id}' is not set up",
                )
            if source_entry.setup_error:
                return NotReady(
                    recording_number=session.recording_number,
                    duration=duration,
                    reason=f"Source '{source_entry.name}' is not ready: {source_entry.setup_error}",
                )
            if source_entry.preview_error:
                return NotReady(
                    recording_number=session.recording_number,
                    duration=duration,
                    reason=f"Source '{source_entry.name}' preview failed: {source_entry.preview_error}",
                )

        group_config = config.all_groups.get(group_id)
        if group_config is None:
            return NotReady(
                recording_number=session.recording_number,
                duration=duration,
                reason=f"Group '{group_id}' is not configured",
            )

        if group.pipeline_errors:
            pipeline_id, error_message = next(iter(group.pipeline_errors.items()))
            pipeline_name = config.pipelines[pipeline_id].name if pipeline_id in config.pipelines else pipeline_id
            return NotReady(
                recording_number=session.recording_number,
                duration=duration,
                reason=f"Pipeline '{pipeline_name}' is not ready: {error_message}",
            )

        if group.preview_error:
            return NotReady(
                recording_number=session.recording_number,
                duration=duration,
                reason=f"Preview is not ready: {group.preview_error}",
            )

        pipeline_configs = [config.pipelines[pipeline_id] for pipeline_id in group_config.pipeline_ids if pipeline_id in config.pipelines]

        try:
            global_placeholder_values = config.global_placeholder_values_dict
            session_placeholder_values = session.get_placeholder_values()
            placeholder_values = resolve_placeholders(global_placeholder_values | session_placeholder_values)
            placeholder_provider = SimplePlaceholderProvider(placeholder_values)
        except UnknownPlaceholderError as exc:
            invalid_placeholder = str(exc).split(": ", 1)[-1]
            return InvalidPlaceholders(
                recording_number=session.recording_number,
                duration=duration,
                message=str(exc),
                invalid_placeholders=[invalid_placeholder],
            )
        except CyclicPlaceholderError as exc:
            return CircularDependency(
                recording_number=session.recording_number,
                duration=duration,
                message=str(exc),
            )

        files = []
        try:
            for pipeline_config in pipeline_configs:
                resolved_config = pipeline_config.active_config.resolve(placeholder_provider)
                files.extend([Path(f) for f in resolved_config.files])
        except Exception as exc:
            return NotReady(
                recording_number=session.recording_number,
                duration=duration,
                reason=f"Session preparation failed: {self._format_exception(exc)}",
            )

        if session.start_error:
            return StartFailed(
                recording_number=session.recording_number,
                duration=duration,
                message=session.start_error,
                files=files,
            )

        return Ready(recording_number=session.recording_number, duration=duration, files=files)

    def _update_active_session(self, group_id: str):
        group = self.groups[group_id]
        active_session_id = group.active_session_id
        if active_session_id:
            state = self._get_session_state(group_id, active_session_id)
        else:
            state = NotReady(reason="No active session", recording_number=group.recording_number)
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

        for placeholder in changes.placeholders_added.values():
            self.placeholder_added.emit(deepcopy(placeholder))
        for old_placeholder, new_placeholder in changes.placeholders_updated.values():
            self.placeholder_changed.emit(deepcopy(new_placeholder))
        for placeholder_id in changes.placeholders_removed:
            self.placeholder_removed.emit(placeholder_id)

    @Slot(str, object, bool)
    def save_config(self, config_file: str, ui_state: object, super_user: bool = False):
        write_protected = False

        if not super_user and os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    write_protected = yaml.safe_load(f).get("write_protected", False)
            except:
                pass

        if write_protected:
            self.error.emit("Config file is write protected. Please save to a different file.", None)
            return

        config_dict = self.config.to_dict()

        with open(config_file, "w+") as f:
            data = {
                "write_protected": super_user,
                "config": config_dict,
                "ui_state": ui_state
            }
            yaml.dump(data, f)

    @Slot(str)
    def load_config(self, config_file: str):
        with open(config_file, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
            config_dict = data["config"]
            ui_state = data["ui_state"]

        new_config = AppConfig.from_dict(config_dict, self.config_types)

        with self.transaction() as config:
            config.settings = new_config.settings
            config.groups = new_config.groups
            config.implicit_groups = new_config.implicit_groups
            config.sources = new_config.sources
            config.pipelines = new_config.pipelines
            config.placeholders = new_config.placeholders

        self.config_loaded.emit(ui_state)
