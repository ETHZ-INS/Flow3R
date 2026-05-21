"""
Runtime controller.

Owns all runtime state (sources, groups, sessions) and every atomic runtime
operation: source/pipeline setup and teardown, preview management, recording
lifecycle, and session-state calculation.

Every method works purely from its own runtime model (self.groups, self.sources)
and the two config-derived snapshots written by Controller after each commit
(runtime_settings, runtime_global_placeholder_values).  The only config-layer
types that cross this boundary are SourceConfig (passed as a parameter to setup
methods) and AppConfig (passed to _sync_group_snapshot and reconcile_runtime so
the runtime can absorb a config snapshot).  No method here reads a ChangeSet or
EffectSet — that orchestration logic lives in Controller.
"""

import traceback
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import reactivex as rx
from reactivex import Subject
from PySide6.QtCore import QObject, Signal, Slot, Qt

from flow3r.logger import get_logger
from flow3r.app.api.app.settings_view import SettingsView
from flow3r.app.api.app.widget_service import WidgetService, SessionWidgetServiceWrapper
from flow3r.app.api.plugins.plugins import PluginAPI
from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.source_config import SourceConfig
from flow3r.app.controller.placeholder_resolver import (
    resolve_placeholders, PlaceholderResolutionError,
    MissingPlaceholderError, CyclicPlaceholderError,
)
from flow3r.app.controller.runtime_model import Group, Preview, Recording, Session, SourceEntry
from flow3r.app.controller.session_state import (
    SessionStateBase,
    Running, FinishingRecording, FinishingProcessing, Finished,
    Ready, StartFailed, NotReady, ViewerOnly, MissingPlaceholder, CircularDependency,
)
from flow3r.core.pipeline.abc.pipeline import (
    ConfigureContext, PreviewContext, PipelineContext,
    CompositePreviewSubscription, CompositePipelineSubscription,
)
from flow3r.core.placeholder.simple_placeholder_provider import SimplePlaceholderProvider
from flow3r.core.source.abc.source import ISource
from flow3r.core.streaming.stream import Stream

_logger = get_logger(__name__)


class ErrorSource(ISource):
    """A source that immediately errors on subscription.

    Used as a stand-in when a real source fails to open, so that downstream
    code always has a valid ISource object to hold on to.
    """

    def __init__(self, exc: Exception):
        self._stream = Stream(None, rx.throw(exc))

    @property
    def stream(self) -> Stream:
        return self._stream

    def open(self):
        pass

    def close(self):
        pass


class RuntimeController(QObject):

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    # Session state — consumed by the UI layer
    session_state_changed = Signal(str, str, SessionStateBase)   # group_id, session_id, state
    active_session_changed = Signal(str, str, SessionStateBase)  # group_id, session_id, state
    active_session_snapshot = Signal(str, str, SessionStateBase) # group_id, session_id, state

    # Recording lifecycle — consumed by the UI layer
    primary_finished = Signal(str, str, object, object)    # group_id, session_id, exc, timestamp
    secondary_finished = Signal(str, str, object, object)  # group_id, session_id, exc, timestamp
    progress_updated = Signal(str, str, object)    # group_id, session_id, progress

    # Recording lifecycle events forwarded to the UI log
    recording_started = Signal(str, str, object)        # group_id, session_id, start_time
    recording_stop_requested = Signal(str, str, object) # group_id, session_id, stop_time

    # Pipeline warnings — emitted when a pipeline calls context.warn(message)
    pipeline_warning = Signal(str, str, str)  # group_id, session_id, message

    # Placeholder values — emitted when a group's active-session placeholder values change
    group_placeholder_values_changed = Signal(str, object)  # group_id, Dict[str, Any]

    # Internal: cross the rx-thread → Qt-main-thread boundary
    _rx_primary_done = Signal(str, str, object, object)    # group_id, session_id, exc, timestamp
    _rx_secondary_done = Signal(str, str, object, object)  # group_id, session_id, exc, timestamp
    _rx_progress = Signal(str, str, object)
    _rx_warning = Signal(str, str, str)  # group_id, session_id, message

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, plugin_api: PluginAPI, widget_service: WidgetService):
        super().__init__()

        self.source_types = plugin_api.source_types.get_source_types()
        self.pipeline_types = plugin_api.pipeline_types.get_pipeline_types()
        self.widget_service = widget_service

        # Runtime state — the single source of truth for all runtime ops
        self.groups: Dict[str, Group] = {}
        self.sources: Dict[str, SourceEntry] = {}

        # Config-derived snapshots written by Controller after each commit
        self.runtime_settings: Dict = {}
        self.runtime_global_placeholder_values: Dict[str, str] = {}
        # Per-group merged placeholder values (global + group-scoped), keyed by group_id.
        # Updated by Controller after each commit whenever placeholder state changes.
        self.runtime_group_placeholder_values: Dict[str, Dict[str, str]] = {}

        # Route recording signals back onto the Qt main thread
        self._rx_primary_done.connect(self._on_primary_done, Qt.ConnectionType.QueuedConnection)
        self._rx_secondary_done.connect(self._on_secondary_done, Qt.ConnectionType.QueuedConnection)
        self._rx_progress.connect(self._on_progress, Qt.ConnectionType.QueuedConnection)
        self._rx_warning.connect(self._on_warning, Qt.ConnectionType.QueuedConnection)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _format_exception(exc: BaseException) -> str:
        message = str(exc).strip()
        return message or exc.__class__.__name__

    # ------------------------------------------------------------------
    # Runtime state helpers — called by Controller after each commit
    # ------------------------------------------------------------------

    def recording_group_ids(self) -> Set[str]:
        """Return IDs of groups that currently have an active recording."""
        result: Set[str] = set()
        for group_id, group in self.groups.items():
            session = group.active_session
            if session is not None and self._session_has_started(session):
                result.add(group_id)
        return result

    @staticmethod
    def _session_has_started(session: Session) -> bool:
        return session.recording is not None and session.recording.start_time is not None

    def is_group_recording(self, group_id: str) -> bool:
        """Return True if the group has an active, unfinished recording."""
        group = self.groups.get(group_id)
        if group is None:
            return False
        return any(
            s.recording and s.recording.start_time and not s.recording.finished
            for s in group.sessions.values()
        )

    def sync_group_snapshot(self, group_id: str, config: AppConfig) -> None:
        """Copy all relevant config fields into the Group runtime object.

        Called after every commit for every group present in both self.groups
        and config.all_groups.  Always overwrites with current committed values.
        """
        group = self.groups.get(group_id)
        group_config = config.all_groups.get(group_id)
        if group is None or group_config is None:
            return

        recording_duration = (
            group_config.recording_config.recording_duration
            if group_config.recording_config.recording_mode == "timed"
            else None
        )
        valid_pipeline_ids = [
            pid for pid in group_config.pipeline_ids if pid in config.pipelines
        ]

        group.group_name = group_config.name
        group.recording_duration = recording_duration
        group.source_ids = [
            sc.id for sc in config.sources.values()
            if sc.implicit_group_id == group_id
        ]
        group.pipeline_ids = valid_pipeline_ids
        group.pipeline_names = {
            pid: config.pipelines[pid].name
            for pid in valid_pipeline_ids
        }
        group.pipeline_type_ids = {
            pid: config.pipelines[pid].pipeline_type
            for pid in valid_pipeline_ids
        }
        group.pipeline_active_configs = {
            pid: config.pipelines[pid].active_config
            for pid in valid_pipeline_ids
        }
        group.pipeline_input_names = {
            pid: list(config.pipelines[pid].active_config.inputs)
            for pid in valid_pipeline_ids
        }
        group.source_mapping = {
            pid: dict(mapping)
            for pid, mapping in group_config.source_mapping.items()
        }
        group.required_placeholder_names = [
            pc.name
            for pc in config.placeholders.values()
            if not pc.is_constant
        ]

    def ensure_active_session(self, group_id: str) -> None:
        """Create an initial session for group_id if none exists yet."""
        group = self.groups.get(group_id)
        if group is None or group.active_session_id is not None:
            return
        session_id = group.new_session()
        group.sessions[session_id].global_placeholder_values = deepcopy(
            self.runtime_group_placeholder_values.get(
                group_id, self.runtime_global_placeholder_values
            )
        )
        self._emit_group_placeholder_values(group_id)

    # ------------------------------------------------------------------
    # Config snapshot propagation — push committed changes into sessions
    # ------------------------------------------------------------------

    def _emit_group_placeholder_values(self, group_id: str) -> None:
        """Emit the current active-session placeholder values for *group_id*."""
        group = self.groups.get(group_id)
        if group and group.active_session:
            self.group_placeholder_values_changed.emit(
                group_id, deepcopy(group.active_session.get_placeholder_values())
            )

    def propagate_group_name(self, group_id: str, new_name: str) -> None:
        """Update the group name on all non-started sessions for this group."""
        group = self.groups.get(group_id)
        if group is None:
            return
        for session in group.sessions.values():
            if not self._session_has_started(session):
                session.group_name = new_name
        self._emit_group_placeholder_values(group_id)

    def propagate_recording_duration(
        self,
        group_id: str,
        new_duration: Optional[float],
        include_started: bool = False,
    ) -> None:
        """Update the recording duration for sessions in this group.

        By default only sessions that have not yet started are updated.
        When *include_started* is ``True``, sessions that are actively
        recording (``Running`` state — i.e. started but not yet stopping)
        are also updated.  Sessions in ``FinishingRecording`` or
        ``FinishingProcessing`` are never touched.
        """
        group = self.groups.get(group_id)
        if group is None:
            return
        for session in group.sessions.values():
            if not self._session_has_started(session):
                session.recording_duration = new_duration
            elif (
                include_started
                and session.recording is not None
                and session.recording.stop_time is None
            ):
                session.recording_duration = new_duration

    def propagate_global_placeholder_values(self, new_global_values: Dict[str, str]) -> None:
        """Update placeholder values on every non-started session across all groups.

        For groups that have per-group placeholder values the merged per-group dict is
        used (because global values are already folded into runtime_group_placeholder_values
        by the controller).  Falls back to *new_global_values* for groups that have no
        per-group customisation.
        """
        for group_id, group in self.groups.items():
            values = self.runtime_group_placeholder_values.get(group_id, new_global_values)
            snapshot = deepcopy(values)
            for session in group.sessions.values():
                if not self._session_has_started(session):
                    session.global_placeholder_values = snapshot
            self._emit_group_placeholder_values(group_id)

    def propagate_group_placeholder_values(self, group_id: str, values: Dict[str, str]) -> None:
        """Update the merged placeholder values for *group_id* and push to non-started sessions."""
        group = self.groups.get(group_id)
        if group is None:
            return
        self.runtime_group_placeholder_values[group_id] = values
        snapshot = deepcopy(values)
        for session in group.sessions.values():
            if not self._session_has_started(session):
                session.global_placeholder_values = snapshot
        self._emit_group_placeholder_values(group_id)

    # ------------------------------------------------------------------
    # Group controls lifecycle
    # ------------------------------------------------------------------

    def set_group_runtime_error(self, group_id: str, error: Optional[str]) -> None:
        group = self.groups.get(group_id)
        if group is not None:
            group.runtime_error = error

    def _set_group_preview_error(self, group_id: str, error: Optional[str]) -> None:
        group = self.groups.get(group_id)
        if group is not None:
            group.preview_error = error

    def _setup_group_controls(self, group_id: str) -> None:
        group = self.groups.get(group_id)
        if group is None:
            return
        self.set_group_runtime_error(group_id, None)
        try:
            if not group.controls_initialized:
                self.widget_service.add_recording_controls(group_id)
                group.controls_initialized = True
            # Location is determined by the UI layer reacting to active_session_changed.
        except Exception as exc:
            self.set_group_runtime_error(group_id, self._format_exception(exc))

    def add_group(self, group_id: str) -> None:
        """Create a Group runtime object and set up its controls widget."""
        if group_id not in self.groups:
            self.groups[group_id] = Group(group_id=group_id, group_name="")
        self._setup_group_controls(group_id)

    def teardown_group(self, group_id: str) -> None:
        group = self.groups.pop(group_id, None)
        if group is None:
            return
        try:
            self.widget_service.remove_recording_controls(group_id)
        except Exception:
            traceback.print_exc()
        for pipeline in group.pipelines.values():
            try:
                pipeline.dispose()
            except Exception:
                traceback.print_exc()

    # ------------------------------------------------------------------
    # Pipeline lifecycle
    # ------------------------------------------------------------------

    def _pipeline_input_mapping(self, group_id: str, pipeline_id: str) -> Dict[str, str]:
        """Return the {input_name: source_id} mapping for pipeline_id."""
        group = self.groups[group_id]
        explicit = group.source_mapping.get(pipeline_id, {})
        if explicit:
            return explicit
        # Single-source / single-input fallback
        input_names = group.pipeline_input_names.get(pipeline_id, [])
        if len(input_names) == 1 and len(group.source_ids) == 1:
            return {input_names[0]: group.source_ids[0]}
        return {}

    def setup_pipeline(self, group_id: str, pipeline_id: str) -> None:
        group = self.groups.get(group_id)
        if group is None:
            return
        if pipeline_id in group.pipelines:
            return

        pipeline_type_id = group.pipeline_type_ids.get(pipeline_id)
        if pipeline_type_id is None:
            group.pipeline_errors[pipeline_id] = "Pipeline type not available in runtime model"
            _logger.error(
                "Pipeline setup failed: type not in runtime model (group=%s, pipeline=%s)",
                group_id, pipeline_id,
            )
            return

        try:
            pipeline_type = self.pipeline_types.get(pipeline_type_id)
            assert pipeline_type is not None, f"Unknown pipeline type: {pipeline_type_id!r}"
            pipeline = pipeline_type.pipeline_factory()
        except Exception as exc:
            group.pipeline_errors[pipeline_id] = self._format_exception(exc)
            _logger.error(
                "Pipeline setup failed (group=%s, pipeline=%s): %s",
                group_id, pipeline_id, exc, exc_info=True,
            )
            return

        group.pipelines[pipeline_id] = pipeline
        self.configure_pipeline(group_id, pipeline_id)

    def configure_pipeline(self, group_id: str, pipeline_id: str) -> None:
        """Resolve placeholders and call pipeline.configure().

        Reads exclusively from the runtime model; never touches AppConfig.
        """
        group = self.groups.get(group_id)
        if group is None:
            return

        pipeline = group.pipelines.get(pipeline_id)
        if pipeline is None:
            group.pipeline_errors[pipeline_id] = "Pipeline is not set up"
            return

        active_session = group.active_session
        if active_session is None:
            group.pipeline_errors[pipeline_id] = "No active session available"
            return

        active_config = group.pipeline_active_configs.get(pipeline_id)
        if active_config is None:
            group.pipeline_errors[pipeline_id] = "Pipeline config not in runtime model"
            return

        try:
            placeholder_values = resolve_placeholders(
                active_session.get_placeholder_values()
            )
            placeholder_provider = SimplePlaceholderProvider(placeholder_values)

            widget_service = SessionWidgetServiceWrapper(self.widget_service, group_id, "preview")

            input_mapping = self._pipeline_input_mapping(group_id, pipeline_id)
            for input_name in active_config.inputs:
                if input_name not in input_mapping:
                    raise Exception(f"Missing source assignment for input '{input_name}'")

            configure_ctx = ConfigureContext(
                active_config.resolve(placeholder_provider),
                SettingsView(self.runtime_settings),
                widget_service,
            )
            pipeline.configure(configure_ctx)
        except PlaceholderResolutionError:
            # A missing/cyclic placeholder is a session-level problem;
            # _get_session_state reports it separately.  Clear any stale
            # pipeline error so it doesn't mask MissingPlaceholder / CircularDependency.
            group.pipeline_errors.pop(pipeline_id, None)
            return
        except Exception as exc:
            group.pipeline_errors[pipeline_id] = self._format_exception(exc)
            return

        group.pipeline_errors.pop(pipeline_id, None)

    def teardown_pipeline(self, group_id: str, pipeline_id: str) -> None:
        group = self.groups.get(group_id)
        if group is None:
            return
        group.pipeline_errors.pop(pipeline_id, None)
        pipeline = group.pipelines.pop(pipeline_id, None)
        if pipeline is not None:
            try:
                pipeline.dispose()
            except Exception:
                traceback.print_exc()

    # ------------------------------------------------------------------
    # Source lifecycle
    # ------------------------------------------------------------------

    def _set_source_setup_error(self, source_id: str, error: Optional[str]) -> None:
        entry = self.sources.get(source_id)
        if entry is not None:
            entry.setup_error = error

    def _set_source_preview_error(self, source_id: str, error: Optional[str]) -> None:
        entry = self.sources.get(source_id)
        if entry is not None:
            entry.preview_error = error

    def setup_source_widget(self, source_config: SourceConfig) -> None:
        if source_config.id not in self.sources:
            self.sources[source_config.id] = SourceEntry()
        entry = self.sources[source_config.id]
        if not entry.widget_handle:
            try:
                entry.widget_handle = self.widget_service.get_source_handle(source_config.id, "preview")
                self._set_source_preview_error(source_config.id, None)
            except Exception as exc:
                self._set_source_preview_error(source_config.id, self._format_exception(exc))

    def teardown_source_widget(self, source_id: str) -> None:
        _logger.debug("Tearing down source '%s'", source_id)
        entry = self.sources.pop(source_id, None)
        if not entry or not entry.widget_handle:
            return
        try:
            entry.widget_handle.dispose()
        except Exception:
            traceback.print_exc()

    def setup_source(self, source_config: SourceConfig) -> None:
        if source_config.id not in self.sources:
            self.sources[source_config.id] = SourceEntry()
        entry = self.sources[source_config.id]
        entry.name = source_config.name
        entry.group_id = source_config.implicit_group_id

        source_type = self.source_types.get(source_config.source_type)
        assert source_type is not None, f"Unknown source type: {source_config.source_type}"

        self._set_source_setup_error(source_config.id, None)

        source = None
        try:
            source = source_type.source_factory(source_config.active_config)
            source.open()
            _logger.debug("Source opened: '%s' (%s)", source_config.name, source_config.id)
        except Exception as exc:
            if source is not None:
                try:
                    source.close()
                except Exception:
                    traceback.print_exc()
            source = ErrorSource(exc)
            self._set_source_setup_error(source_config.id, self._format_exception(exc))
            _logger.error(
                "Source setup failed: '%s' (%s) — %s",
                source_config.name, source_config.id, exc, exc_info=True,
            )
            try:
                source.open()
            except Exception:
                pass

        entry.source = source

    def teardown_source(self, source_id: str) -> None:
        _logger.debug("Tearing down source '%s'", source_id)
        entry = self.sources.get(source_id)
        if not entry or not entry.source:
            return
        try:
            entry.source.close()
        except Exception:
            traceback.print_exc()
        entry.source = None

    def start_preview(self, source_id: str) -> None:
        entry = self.sources.get(source_id)
        if entry is None:
            return
        if entry.source is None:
            self._set_source_preview_error(source_id, "Source is not available")
            return
        if entry.widget_handle is None:
            self._set_source_preview_error(source_id, "Preview widget is not available")
            return
        if entry.preview_sub is not None:
            return

        widget_handle = entry.widget_handle
        self._set_source_preview_error(source_id, None)

        try:
            widget_handle.set_error(None)
            widget_handle.set_format(entry.source.stream.format)

            def _on_preview_error(exc: Exception):
                entry.preview_sub = None
                if entry.setup_error is None:
                    self._set_source_preview_error(source_id, self._format_exception(exc))
                widget_handle.set_error(exc)
                self._refresh_group_state(entry.group_id)

            entry.preview_sub = entry.source.stream.data.subscribe(
                on_next=widget_handle.set_item,
                on_error=_on_preview_error,
                on_completed=lambda: widget_handle.set_completed(True),
            )
        except Exception as exc:
            self._set_source_preview_error(source_id, self._format_exception(exc))
            try:
                widget_handle.set_error(exc)
            except Exception:
                traceback.print_exc()

    def stop_preview(self, source_id: str) -> None:
        _logger.debug("Stopping source preview for '%s'", source_id)
        entry = self.sources.get(source_id)
        if not entry or not entry.preview_sub:
            return
        try:
            entry.preview_sub.dispose()
        except Exception:
            traceback.print_exc()
        entry.preview_sub = None

    # ------------------------------------------------------------------
    # Pipeline preview
    # ------------------------------------------------------------------

    def stop_pipeline_preview(self, group_id: str) -> None:
        group = self.groups.get(group_id)
        if group is None or group.preview is None:
            return
        if group.preview.preview_sub is not None:
            try:
                group.preview.preview_sub.dispose()
                _logger.debug("Disposed pipeline preview subscription for group '%s'", group_id)
            except Exception:
                traceback.print_exc()
        for connection in group.preview.connections:
            try:
                connection.dispose()
            except Exception:
                traceback.print_exc()
        group.preview = None

    def start_pipeline_preview(self, group_id: str) -> None:
        """Build and start a pipeline preview, reading only from the runtime model."""
        from reactivex import operators as ops

        group = self.groups.get(group_id)
        if group is None:
            return

        self._set_group_preview_error(group_id, None)

        if not group.pipeline_ids:
            return
        if group.preview is not None:
            return  # already running

        # Re-configure each pipeline so it picks up any recent changes.
        for pipeline_id in group.pipeline_ids:
            self.configure_pipeline(group_id, pipeline_id)

        # Abort if any assigned pipeline failed to configure.
        assigned = set(group.pipeline_ids)
        blocking_errors = {pid: err for pid, err in group.pipeline_errors.items() if pid in assigned}
        if blocking_errors:
            pid, err = next(iter(blocking_errors.items()))
            self._set_group_preview_error(
                group_id,
                f"Pipeline '{group.pipeline_names.get(pid, pid)}' is not ready: {err}",
            )
            return

        # Abort if any assigned pipeline has no instance yet.
        missing = [pid for pid in group.pipeline_ids if pid not in group.pipelines]
        if missing:
            self._set_group_preview_error(group_id, f"Pipelines are not set up: {', '.join(missing)}")
            return

        # Abort if any pipeline's input mapping is incomplete.
        for pipeline_id in group.pipeline_ids:
            input_mapping = self._pipeline_input_mapping(group_id, pipeline_id)
            for input_name in group.pipeline_input_names.get(pipeline_id, []):
                if input_name not in input_mapping:
                    self._set_group_preview_error(group_id, "Preview input mapping is incomplete")
                    return

        # Build one Stream per (pipeline, input) pair.
        source_observables = []
        source_streams: Dict[str, Dict] = {}
        try:
            for pipeline_id in group.pipeline_ids:
                source_streams[pipeline_id] = {}
                input_mapping = self._pipeline_input_mapping(group_id, pipeline_id)
                for input_name in group.pipeline_input_names.get(pipeline_id, []):
                    source_id = input_mapping.get(input_name)
                    if source_id is None:
                        name = group.pipeline_names.get(pipeline_id, pipeline_id)
                        raise Exception(
                            f"Pipeline '{name}' is missing a source assignment for input '{input_name}'"
                        )
                    entry = self.sources.get(source_id)
                    if entry is None or entry.source is None:
                        raise Exception(f"Source '{source_id}' is not available")
                    if entry.setup_error:
                        raise Exception(f"Source '{entry.name}' is not ready: {entry.setup_error}")
                    observable = entry.source.stream.data.pipe(ops.publish())
                    source_observables.append(observable)
                    source_streams[pipeline_id][input_name] = Stream(
                        entry.source.stream.format, observable, entry.name
                    )
        except Exception as exc:
            self._set_group_preview_error(group_id, self._format_exception(exc))
            return

        # Ask each pipeline to build its preview subscription.
        try:
            active_session = group.active_session
            try:
                placeholder_values = resolve_placeholders(
                    active_session.get_placeholder_values()
                )
                placeholder_provider = SimplePlaceholderProvider(placeholder_values)
            except PlaceholderResolutionError:
                return  # already surfaced via pipeline_errors; avoid duplicate error

            settings_view = SettingsView(self.runtime_settings)
            preview_subs = []
            for pipeline_id in group.pipeline_ids:
                pipeline = group.pipelines[pipeline_id]
                if not pipeline.supports_preview:
                    continue
                name = group.pipeline_names.get(pipeline_id, pipeline_id)
                active_config = group.pipeline_active_configs.get(pipeline_id)
                try:
                    ctx = PreviewContext(
                        active_config.resolve(placeholder_provider),
                        settings_view,
                        SessionWidgetServiceWrapper(self.widget_service, group_id, "preview"),
                    )
                    pipeline.preview(ctx, source_streams[pipeline_id])
                    preview_subs.append(ctx.build_subscription())
                except Exception as exc:
                    for ps in preview_subs:
                        try:
                            ps.dispose()
                        except Exception:
                            traceback.print_exc()
                    raise Exception(
                        f"Pipeline '{name}' preview failed: {self._format_exception(exc)}"
                    ) from exc

            if not preview_subs:
                return  # no pipeline in the group supports preview; nothing to start

            preview_sub = CompositePreviewSubscription(preview_subs)
        except Exception as exc:
            self._set_group_preview_error(group_id, self._format_exception(exc))
            return

        def _preview_done(_):
            _logger.debug("Pipeline preview completed for group '%s'", group_id)

        def _preview_failed(exc: Exception):
            _logger.warning("Pipeline preview failed for group '%s': %s", group_id, exc)
            self.stop_pipeline_preview(group_id)
            self._set_group_preview_error(group_id, self._format_exception(exc))
            self._refresh_group_state(group_id)

        preview_sub.done.pipe(ops.take(1)).subscribe(_preview_done, _preview_failed)

        connections = [obs.connect() for obs in source_observables]
        group.preview = Preview(connections, preview_sub)

    # ------------------------------------------------------------------
    # Session-state calculation
    # ------------------------------------------------------------------

    def _get_session_state(self, group_id: str, session_id: str) -> SessionStateBase:
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"
        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found"

        duration = session.recording_duration

        # --- Recording / finishing states ---
        if session.recording and session.recording.start_time:
            start_time = session.recording.start_time
            stop_time = session.recording.stop_time
            if stop_time:
                if session.recording.primary_finished:
                    if session.recording.secondary_finished:
                        return Finished(
                            recording_number=session.recording_number,
                            start_time=start_time, stop_time=stop_time,
                            end_time=stop_time, duration=duration,
                        )
                    return FinishingProcessing(
                        recording_number=session.recording_number,
                        start_time=start_time, stop_time=stop_time,
                        duration=duration,
                    )
                return FinishingRecording(
                    recording_number=session.recording_number,
                    start_time=start_time, stop_time=stop_time,
                    duration=duration,
                )
            return Running(
                recording_number=session.recording_number,
                start_time=start_time, duration=duration,
            )

        # --- Pre-recording readiness checks ---
        if group.runtime_error:
            return NotReady(
                recording_number=session.recording_number, duration=duration,
                reason=f"Group '{group.group_name}' is not ready: {group.runtime_error}",
            )

        for source_id in group.source_ids:
            entry = self.sources.get(source_id)
            if entry is None:
                return NotReady(
                    recording_number=session.recording_number, duration=duration,
                    reason=f"Source '{source_id}' is not set up",
                )
            if entry.setup_error:
                return NotReady(
                    recording_number=session.recording_number, duration=duration,
                    reason=f"Source '{entry.name}' is not ready: {entry.setup_error}",
                )
            if entry.preview_error:
                return NotReady(
                    recording_number=session.recording_number, duration=duration,
                    reason=f"Source '{entry.name}' preview failed: {entry.preview_error}",
                )

        if not group.pipeline_ids:
            return ViewerOnly(recording_number=session.recording_number, duration=duration)

        # --- Placeholder resolution (checked before pipeline_errors so that a
        #     missing/cyclic placeholder wins over any derivative pipeline error) ---

        # Explicitly check every defined (non-constant) placeholder has a value.
        # resolve_placeholders only raises MissingPlaceholderError when a value
        # *references* an absent name via {token} syntax; a standalone unset
        # placeholder would pass through silently without this guard.
        raw_placeholder_values = session.get_placeholder_values()
        for name in group.required_placeholder_names:
            if name not in raw_placeholder_values:
                return MissingPlaceholder(
                    recording_number=session.recording_number, duration=duration,
                    message=f"Missing placeholder: {name}", placeholder_name=name,
                )

        try:
            placeholder_values = resolve_placeholders(raw_placeholder_values)
            placeholder_provider = SimplePlaceholderProvider(placeholder_values)
        except MissingPlaceholderError as exc:
            return MissingPlaceholder(
                recording_number=session.recording_number, duration=duration,
                message=str(exc), placeholder_name=exc.placeholder_name,
            )
        except CyclicPlaceholderError as exc:
            return CircularDependency(
                recording_number=session.recording_number, duration=duration,
                message=str(exc),
            )

        if group.pipeline_errors:
            pid, msg = next(iter(group.pipeline_errors.items()))
            return NotReady(
                recording_number=session.recording_number, duration=duration,
                reason=f"Pipeline '{group.pipeline_names.get(pid, pid)}' is not ready: {msg}",
            )

        # If every configured pipeline is viewer-only, recording is not available.
        if all(
            not group.pipelines[pid].supports_recording
            for pid in group.pipeline_ids
            if pid in group.pipelines
        ):
            return ViewerOnly(recording_number=session.recording_number, duration=duration)

        if group.preview_error:
            return NotReady(
                recording_number=session.recording_number, duration=duration,
                reason=f"Preview is not ready: {group.preview_error}",
            )

        # --- File list derivation ---
        files: List[Path] = []
        try:
            for pid in group.pipeline_ids:
                active_config = group.pipeline_active_configs.get(pid)
                if active_config is not None:
                    files.extend(Path(f) for f in active_config.resolve(placeholder_provider).files)
        except Exception as exc:
            traceback.print_exc()
            return NotReady(
                recording_number=session.recording_number, duration=duration,
                reason=f"Session preparation failed: {self._format_exception(exc)}",
            )

        if session.start_error:
            return StartFailed(
                recording_number=session.recording_number, duration=duration,
                message=session.start_error, files=files,
            )

        return Ready(recording_number=session.recording_number, duration=duration, files=files)

    def _update_session_state(self, group_id: str, session_id: str) -> None:
        state = self._get_session_state(group_id, session_id)
        _logger.debug("Session state for '%s': %s", session_id, state)
        self.session_state_changed.emit(group_id, session_id, state)

    def _update_active_session(self, group_id: str) -> None:
        group = self.groups.get(group_id)
        if group is None:
            return
        active_session_id = group.active_session_id
        if active_session_id:
            state = self._get_session_state(group_id, active_session_id)
        else:
            state = NotReady(reason="No active session", recording_number=group.next_recording_number)
        self.active_session_changed.emit(group_id, active_session_id, state)

    def _refresh_group_state(self, group_id: str) -> None:
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

    def refresh_all_group_states(self) -> None:
        for group_id in list(self.groups):
            self._refresh_group_state(group_id)

    # ------------------------------------------------------------------
    # Recording number management
    # ------------------------------------------------------------------

    def set_recording_number(self, group_id: str, number: int) -> None:
        """Set the recording number for a group to a specific value.

        If there is an active session that has not yet started recording, it
        immediately receives *number* as its recording_number and the group
        counter advances to ``number + 1`` so the following session continues
        from the right place.

        If there is no pending session (or the active one is already recording),
        *number* is stored as next_recording_number so the next call to
        new_session() picks it up.
        """
        group = self.groups.get(group_id)
        if group is None:
            _logger.warning("set_recording_number: unknown group %s", group_id)
            return
        number = max(1, number)
        session = group.active_session
        if session is not None and (session.recording is None or session.recording.start_time is None):
            # Pending session exists — give it this number, advance counter past it.
            session.recording_number = number
            group.next_recording_number = number + 1
        else:
            # No pending session — just set the counter; new_session() will use it.
            group.next_recording_number = number
        _logger.info(
            "Recording number for group %s (%s) set to %d",
            group.group_name, group_id, number,
        )
        self._emit_group_placeholder_values(group_id)
        self._refresh_group_state(group_id)

    # ------------------------------------------------------------------
    # Snapshot requests
    # ------------------------------------------------------------------

    @Slot(str)
    def send_active_session_snapshot(self, group_id: str) -> None:
        group = self.groups.get(group_id)
        if group and group.active_session_id:
            state = self._get_session_state(group_id, group.active_session_id)
            self.active_session_snapshot.emit(group_id, group.active_session_id, state)

    @Slot()
    def send_group_placeholder_snapshots(self) -> None:
        """Emit current placeholder values for every group that has an active session."""
        for group in self.groups.values():
            if group.active_session:
                self.group_placeholder_values_changed.emit(
                    group.group_id, deepcopy(group.active_session.get_placeholder_values())
                )

    # ------------------------------------------------------------------
    # Full runtime reconciliation (called by Controller.reconcile_runtime)
    # ------------------------------------------------------------------

    def reconcile_runtime(self, config: AppConfig) -> None:
        """Reconcile the full runtime state against the given committed config."""

        # --- Groups: remove stale, create missing ---
        for group_id in list(self.groups):
            if group_id not in config.all_groups:
                try:
                    self.teardown_group(group_id)
                except Exception:
                    traceback.print_exc()

        for group_id in config.all_groups:
            try:
                if group_id not in self.groups:
                    self.groups[group_id] = Group(group_id=group_id, group_name="")
                self._setup_group_controls(group_id)
                self.sync_group_snapshot(group_id, config)
                self.ensure_active_session(group_id)
            except Exception as exc:
                self.set_group_runtime_error(group_id, self._format_exception(exc))

        # --- Sources: remove stale, set up missing ---
        for source_id in list(self.sources):
            if source_id not in config.sources:
                try:
                    self.stop_preview(source_id)
                    self.teardown_source(source_id)
                    self.teardown_source_widget(source_id)
                except Exception:
                    traceback.print_exc()

        for source_config in config.sources.values():
            try:
                self.setup_source_widget(source_config)
                self.setup_source(source_config)
                self.start_preview(source_config.id)
            except Exception as exc:
                msg = self._format_exception(exc)
                self._set_source_setup_error(source_config.id, msg)
                self._set_source_preview_error(source_config.id, msg)

        # --- Pipelines: tear down stale, set up / configure missing ---
        for group_id, group in self.groups.items():
            desired = set(group.pipeline_ids)
            for pipeline_id in list(group.pipelines):
                if pipeline_id not in desired:
                    try:
                        self.teardown_pipeline(group_id, pipeline_id)
                    except Exception:
                        traceback.print_exc()
            for pipeline_id in desired:
                try:
                    self.setup_pipeline(group_id, pipeline_id)
                except Exception as exc:
                    group.pipeline_errors[pipeline_id] = self._format_exception(exc)

        # --- Pipeline previews: start for groups that aren't recording ---
        for group_id, group in self.groups.items():
            session = group.active_session
            if session is None or not self._session_has_started(session):
                self.start_pipeline_preview(group_id)

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------

    def _set_session_start_error(self, group_id: str, session_id: str, error: Optional[str]) -> None:
        group = self.groups.get(group_id)
        if group is None:
            return
        session = group.sessions.get(session_id)
        if session is not None:
            session.start_error = error

    def _dispose_recording_resources(self, recording: Optional[Recording]) -> None:
        if recording is None:
            return
        if recording.pipeline_sub is not None:
            try:
                recording.pipeline_sub.dispose()
            except Exception:
                traceback.print_exc()
        for connection in recording.connections or []:
            try:
                connection.dispose()
            except Exception:
                traceback.print_exc()

    def _fail_recording_start(
        self,
        group_id: str,
        session_id: str,
        error: str,
        *,
        recording: Optional[Recording] = None,
        restart_preview: bool = False,
    ) -> None:
        _logger.error(
            "Recording start failed (group=%s, session=%s): %s",
            group_id, session_id, error,
        )
        if recording is not None:
            self._dispose_recording_resources(recording)
        self._set_session_start_error(group_id, session_id, error)
        if restart_preview:
            self.start_pipeline_preview(group_id)
        self._refresh_group_state(group_id)

    def _recording_finished(self, group_id: str, session_id: str) -> None:
        group = self.groups.get(group_id)
        assert group is not None
        session = group.sessions.get(session_id)
        assert session is not None

        if not session.recording or session.recording.finished:
            return

        if session.recording.stop_time is None:
            session.recording.stop_time = datetime.now()

        duration = (
            session.recording.stop_time - session.recording.start_time
        ).total_seconds() if session.recording.start_time else None

        session.recording.finished = True
        self._dispose_recording_resources(session.recording)

        _logger.info(
            "Recording finished (group=%s, session=%s, duration=%.1fs)",
            group_id, session_id, duration if duration is not None else 0.0,
        )

        # Create the next session, seeding it from the current runtime snapshots.
        new_session_id = group.new_session()
        group.sessions[new_session_id].global_placeholder_values = deepcopy(
            self.runtime_group_placeholder_values.get(
                group_id, self.runtime_global_placeholder_values
            )
        )

        self._update_active_session(group_id)
        self._update_session_state(group_id, session_id)
        self.start_pipeline_preview(group_id)
        self._refresh_group_state(group_id)
        self._emit_group_placeholder_values(group_id)

    # ------------------------------------------------------------------
    # Recording — start / stop
    # ------------------------------------------------------------------

    @Slot(str, str)
    def start_recording(self, group_id: str, session_id: str) -> None:
        from reactivex import operators as ops

        group = self.groups.get(group_id)
        if group is None:
            return
        session = group.sessions.get(session_id)
        if session is None:
            return
        if session.recording and session.recording.start_time:
            return

        self._set_session_start_error(group_id, session_id, None)

        if group.runtime_error:
            self._refresh_group_state(group_id)
            return
        if group.pipeline_errors:
            self._refresh_group_state(group_id)
            return
        if not group.pipeline_ids:
            self._fail_recording_start(group_id, session_id, "No pipelines configured")
            return

        missing = [pid for pid in group.pipeline_ids if pid not in group.pipelines]
        if missing:
            self._fail_recording_start(
                group_id, session_id, f"Pipelines are not set up: {', '.join(missing)}"
            )
            return

        # Build gated source streams (one per pipeline input).
        recording = Recording(Subject(), Subject(), Subject())
        source_observables = []
        source_streams: Dict[str, Dict] = {}
        try:
            for pipeline_id in group.pipeline_ids:
                source_streams[pipeline_id] = {}
                input_mapping = self._pipeline_input_mapping(group_id, pipeline_id)
                for input_name in group.pipeline_input_names.get(pipeline_id, []):
                    source_id = input_mapping.get(input_name)
                    if source_id is None:
                        name = group.pipeline_names.get(pipeline_id, pipeline_id)
                        raise Exception(
                            f"Pipeline '{name}' is missing a source assignment for input '{input_name}'"
                        )
                    entry = self.sources.get(source_id)
                    if entry is None or entry.source is None:
                        raise Exception(f"Source '{source_id}' is not available")
                    if entry.setup_error:
                        raise Exception(f"Source '{entry.name}' is not ready: {entry.setup_error}")
                    observable = entry.source.stream.data.pipe(ops.publish())
                    source_observables.append(observable)
                    gated = observable.pipe(
                        ops.skip_until(recording.start),
                        ops.take_until(recording.stop),
                    )
                    source_streams[pipeline_id][input_name] = Stream(
                        entry.source.stream.format, gated, name=entry.name
                    )
        except Exception as exc:
            self._fail_recording_start(group_id, session_id, self._format_exception(exc))
            return

        preview_was_running = group.preview is not None
        if preview_was_running:
            self.stop_pipeline_preview(group_id)

        try:
            placeholder_values = resolve_placeholders(
                session.get_placeholder_values()
            )
            placeholder_provider = SimplePlaceholderProvider(placeholder_values)
            settings_view = SettingsView(self.runtime_settings)

            pipeline_subs = []
            for pipeline_id in group.pipeline_ids:
                active_config = group.pipeline_active_configs[pipeline_id]
                name = group.pipeline_names.get(pipeline_id, pipeline_id)
                pipeline = group.pipelines[pipeline_id]
                if not pipeline.supports_recording:
                    continue
                resolved_config = active_config.resolve(placeholder_provider)
                widget_svc = SessionWidgetServiceWrapper(self.widget_service, group_id, session_id)
                try:
                    pipeline.configure(ConfigureContext(resolved_config, settings_view, widget_svc))
                    build_ctx = PipelineContext(resolved_config, settings_view, widget_svc, recording.control)
                    pipeline.build(build_ctx, source_streams[pipeline_id])
                    pipeline_subs.append(build_ctx.build_subscription())
                except Exception:
                    for ps in pipeline_subs:
                        try:
                            ps.dispose()
                        except Exception:
                            traceback.print_exc()
                    raise

            if not pipeline_subs:
                raise Exception("No pipelines in this group support recording")

            recording.pipeline_sub = CompositePipelineSubscription(pipeline_subs)
            recording.start_time = datetime.now()
            recording.connections = [obs.connect() for obs in source_observables]
            session.recording = recording
            recording.start.on_next(None)
            recording.control.on_next(None)
            self.recording_started.emit(group_id, session_id, recording.start_time)
            _logger.info(
                "Recording started (group=%s, session=%s, started_at=%s)",
                group_id, session_id, recording.start_time.isoformat(timespec="seconds"),
            )

        except Exception as exc:
            self._fail_recording_start(
                group_id, session_id, self._format_exception(exc),
                recording=recording, restart_preview=preview_was_running,
            )
            return

        def _primary_done(_):
            self._rx_primary_done.emit(group_id, session_id, None, datetime.now())

        def _primary_failed(exc: Exception):
            self._rx_primary_done.emit(group_id, session_id, exc, datetime.now())

        def _secondary_done(_):
            self._rx_secondary_done.emit(group_id, session_id, None, datetime.now())

        def _secondary_failed(exc: Exception):
            traceback.print_tb(exc.__traceback__)
            self._rx_secondary_done.emit(group_id, session_id, exc, datetime.now())

        def _progress_cb(progress: Tuple[int, int]):
            self._rx_progress.emit(group_id, session_id, progress)

        assert session.recording.pipeline_sub is not None
        session.recording.pipeline_sub.primary_done.pipe(ops.take(1)).subscribe(
            _primary_done, _primary_failed
        )
        session.recording.pipeline_sub.secondary_done.pipe(ops.take(1)).subscribe(
            _secondary_done, _secondary_failed
        )
        if session.recording.pipeline_sub.progress:
            session.recording.pipeline_sub.progress.subscribe(_progress_cb)

        self._refresh_group_state(group_id)

    @Slot(str, str)
    def stop_recording(self, group_id: str, session_id: str) -> None:
        group = self.groups.get(group_id)
        assert group is not None, f"Group {group_id} not found"
        session = group.sessions.get(session_id)
        assert session is not None, f"Session {session_id} not found"

        if session.recording and not session.recording.stop_time:
            session.recording.stop_time = datetime.now()
            self.recording_stop_requested.emit(group_id, session_id, session.recording.stop_time)
            _logger.info(
                "Recording stop requested (group=%s, session=%s, stopped_at=%s)",
                group_id, session_id,
                session.recording.stop_time.isoformat(timespec="seconds"),
            )
            session.recording.stop.on_next(None)
            if not session.recording.control.is_stopped:
                session.recording.control.on_completed()

        self._update_session_state(group_id, session_id)

    # ------------------------------------------------------------------
    # Recording lifecycle — signal handlers (QueuedConnection, main thread)
    # ------------------------------------------------------------------

    @Slot(str, str, str)
    def _on_warning(self, group_id: str, session_id: str, message: str) -> None:
        """Re-emit a pipeline warning on the Qt main thread as a public signal."""
        self.pipeline_warning.emit(group_id, session_id, message)

    @Slot(str, str, object, object)
    def _on_primary_done(self, group_id: str, session_id: str, exc: Optional[Exception], timestamp: datetime) -> None:
        group = self.groups.get(group_id)
        assert group is not None
        session = group.sessions.get(session_id)
        assert session is not None

        if session.recording:
            if session.recording.primary_finished:
                return
            session.recording.primary_finished = True
            session.recording.acquisition_finished_time = timestamp
            if exc:
                _logger.error(
                    "Primary recording pipeline failed (group=%s, session=%s): %s",
                    group_id, session_id, exc, exc_info=exc,
                )
            else:
                _logger.info("Primary recording pipeline done (group=%s, session=%s)", group_id, session_id)
            if session.recording.secondary_finished:
                self._recording_finished(group_id, session_id)

        self._update_session_state(group_id, session_id)
        self.primary_finished.emit(group_id, session_id, exc, timestamp)

    @Slot(str, str, object, object)
    def _on_secondary_done(self, group_id: str, session_id: str, exc: Optional[Exception], timestamp: datetime) -> None:
        group = self.groups.get(group_id)
        assert group is not None
        session = group.sessions.get(session_id)
        assert session is not None

        if session.recording:
            if session.recording.secondary_finished:
                return
            session.recording.secondary_finished = True
            session.recording.processing_finished_time = timestamp
            if exc:
                _logger.error(
                    "Secondary recording pipeline failed (group=%s, session=%s): %s",
                    group_id, session_id, exc, exc_info=exc,
                )
            else:
                _logger.info(
                    "Secondary recording pipeline done (group=%s, session=%s)", group_id, session_id
                )
            if session.recording.primary_finished:
                self._recording_finished(group_id, session_id)

        self._update_session_state(group_id, session_id)
        if session.recording and session.recording.stop_time is not None:
            self.secondary_finished.emit(group_id, session_id, exc, timestamp)

    @Slot(str, str, object)
    def _on_progress(self, group_id: str, session_id: str, progress: Tuple[int, int]) -> None:
        group = self.groups.get(group_id)
        assert group is not None
        session = group.sessions.get(session_id)
        assert session is not None

        if session.recording:
            session.recording.progress = progress

        self._update_session_state(group_id, session_id)
        self.progress_updated.emit(group_id, session_id, progress)

