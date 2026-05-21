"""
Controller — configuration management layer.

Owns the committed AppConfig and all operations that read or write it
(transactions, CRUD slots, config repair/validation, persistence).

Runtime operations (source/pipeline lifecycle, preview, recording,
session-state calculation) are fully delegated to self.runtime
(RuntimeController).  The only points where the two layers touch are:

  - _commit(): updates self._config, writes runtime_settings and
    runtime_global_placeholder_values onto self.runtime, then calls
    self.runtime._apply_runtime_changes() and
    self.runtime._refresh_all_group_states().

  - setup_source() slot: reads self._config to obtain the SourceConfig,
    then delegates entirely to self.runtime.

  - reconcile_runtime() slot: delegates to
    self.runtime.reconcile_runtime(self._config).
"""

import os
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, OrderedDict

import yaml
from PySide6.QtCore import QObject, Signal, Slot

from flow3r.logger import get_logger
from flow3r.app.api.plugins.plugins import PluginAPI
from flow3r.app.api.app.widget_service import WidgetService
from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.group_config import GroupConfig
from flow3r.app.config.pipeline_config import PipelineConfig
from flow3r.app.config.placeholder_config import PlaceholderConfig
from flow3r.app.config.source_config import SourceConfig
from flow3r.app.controller.commit import ConfigChangeReply, Transaction
from flow3r.app.controller.config_diff import ChangeSet, EffectSet, calculate_effects, diff_config
from flow3r.app.controller.runtime_controller import RuntimeController
from flow3r.app.controller.session_state import SessionStateBase

_logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _flat_diff(old: dict, new: dict, prefix: str = "") -> list:
    """Recursively diff two plain dicts and return human-readable change strings.

    Each entry has the form ``"dotted.key.path: <old> → <new>"``.
    Leaf values are repr-capped at 120 characters so that large blobs
    (e.g. full file paths or binary config data) don't flood the log.
    """
    result = []
    sep = "." if prefix else ""
    for k in sorted(set(old) | set(new), key=str):
        path = f"{prefix}{sep}{k}"
        old_v = old.get(k, "<absent>")
        new_v = new.get(k, "<absent>")
        if old_v == new_v:
            continue
        if isinstance(old_v, dict) and isinstance(new_v, dict):
            result.extend(_flat_diff(old_v, new_v, path))
        else:
            def _r(v):
                s = repr(v)
                return s if len(s) <= 120 else s[:117] + "..."
            result.append(f"{path}: {_r(old_v)} → {_r(new_v)}")
    return result


def _fmt_source(sc) -> str:
    return (
        f"name={sc.name!r}  id={sc.id}  type={sc.source_type!r}"
        f"  group={sc.group_id!r}  active={sc.active}"
    )


def _fmt_group(gc) -> str:
    return (
        f"name={gc.name!r}  id={gc.id}"
        f"  recording_mode={gc.recording_config.recording_mode!r}"
        f"  pipelines={sorted(gc.pipeline_ids)}"
    )


def _fmt_pipeline(pc) -> str:
    return f"name={pc.name!r}  id={pc.id}  type={pc.pipeline_type!r}"


def _fmt_placeholder(pc) -> str:
    return (
        f"name={pc.name!r}  id={pc.id}  label={pc.label!r}"
        f"  type={pc.type!r}  constant={pc.is_constant}"
        + (f"  value={pc.constant_value!r}" if pc.is_constant else "")
    )


class Controller(QObject):

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    # (message, level) where level is "INFO", "WARNING", or "ERROR"
    log_message = Signal(str, str)

    # Settings
    settings_snapshot = Signal(object)
    settings_changed = Signal(object)

    # Full config snapshot / change
    config_snapshot = Signal(AppConfig)
    config_changed = Signal(AppConfig)
    persistent_config_changed = Signal(AppConfig)  # fired only when on-disk state changes

    # Errors
    error = Signal(str, object)

    # Sources
    source_snapshot = Signal(SourceConfig)
    source_added = Signal(SourceConfig)
    source_changed = Signal(SourceConfig)
    source_removed = Signal(str)

    # Groups
    group_snapshot = Signal(GroupConfig)
    group_added = Signal(GroupConfig)
    group_changed = Signal(GroupConfig)
    group_removed = Signal(str)

    # Pipelines
    pipeline_added = Signal(PipelineConfig)
    pipeline_changed = Signal(PipelineConfig)
    pipeline_removed = Signal(str)

    # Placeholders
    placeholder_added = Signal(PlaceholderConfig)
    placeholder_changed = Signal(PlaceholderConfig)
    placeholder_removed = Signal(str)

    # Session state — forwarded from self.runtime
    active_session_snapshot = Signal(str, str, SessionStateBase)
    active_session_changed = Signal(str, str, SessionStateBase)
    session_state_changed = Signal(str, str, SessionStateBase)

    # Recording lifecycle — forwarded from self.runtime
    primary_finished = Signal(str, str, object, object)    # group_id, session_id, exc, timestamp
    secondary_finished = Signal(str, str, object, object)  # group_id, session_id, exc, timestamp
    progress_updated = Signal(str, str, object)
    recording_started = Signal(str, str, object)        # group_id, session_id, start_time
    recording_stop_requested = Signal(str, str, object) # group_id, session_id, stop_time

    # Placeholder values — forwarded from self.runtime
    group_placeholder_values_changed = Signal(str, object)  # group_id, Dict[str, Any]

    # Pipeline warnings — call context.warn(msg) inside a pipeline to emit this
    pipeline_warning = Signal(str, str, str)  # group_id, session_id, message

    # Persistence
    config_loaded = Signal(object)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, plugin_api: PluginAPI, widget_service: WidgetService):
        super().__init__()

        self.config_types = plugin_api.config_types.config_types

        # Committed configuration — the only config-layer state.
        self._config = AppConfig()

        # Transaction state
        self._draft: Optional[Transaction] = None
        self._in_tx: int = 0

        # Runtime layer — owns all live sources, groups, sessions, pipelines.
        self.runtime = RuntimeController(plugin_api, widget_service)

        # Forward runtime signals to this controller's public signals so that
        # existing UI code connecting to controller.* continues to work.
        self.runtime.session_state_changed.connect(self.session_state_changed)
        self.runtime.active_session_changed.connect(self.active_session_changed)
        self.runtime.active_session_snapshot.connect(self.active_session_snapshot)
        self.runtime.primary_finished.connect(self.primary_finished)
        self.runtime.secondary_finished.connect(self.secondary_finished)
        self.runtime.progress_updated.connect(self.progress_updated)
        self.runtime.recording_started.connect(self.recording_started)
        self.runtime.recording_stop_requested.connect(self.recording_stop_requested)
        self.runtime.pipeline_warning.connect(self.pipeline_warning)
        self.runtime.group_placeholder_values_changed.connect(self.group_placeholder_values_changed)

    # ------------------------------------------------------------------
    # Config property
    # ------------------------------------------------------------------

    @property
    def config(self) -> AppConfig:
        """Return a deep copy of the committed configuration."""
        return deepcopy(self._config)

    # ------------------------------------------------------------------
    # Transaction / commit
    # ------------------------------------------------------------------

    @contextmanager
    def transaction(self, reply: Optional[ConfigChangeReply] = None) -> Iterator[Transaction]:
        """Context manager that yields a mutable :class:`Transaction`.

        The transaction's ``config`` field is a deep-copy draft of the
        committed config.  Callers edit ``tx.config`` and set any
        per-transaction flags (e.g. ``tx.propagate_duration_group_ids``)
        before the block exits.

        On clean exit the draft is committed (config signals are emitted and
        the runtime hook is called).  On exception the draft is discarded and
        the error signal is emitted.

        Nested transactions reuse the same :class:`Transaction`; only the
        outermost exit triggers a commit.
        """
        if self._in_tx != 0:
            self._in_tx += 1
            try:
                yield self._draft  # type: ignore[misc]
            finally:
                self._in_tx -= 1
            return

        self._in_tx = 1
        self._draft = Transaction(config=deepcopy(self._config))
        try:
            assert self._draft is not None
            yield self._draft
            self._commit(self._draft)
            if reply:
                reply.finished.emit(True, None)
        except Exception as exc:
            _logger.error("Config transaction failed: %s", exc, exc_info=True)
            self.error.emit("Config change failed", exc)
            if reply:
                reply.finished.emit(False, exc)
        finally:
            self._draft = None
            self._in_tx = 0

    def _commit(self, tx: Transaction) -> None:
        """Validate, diff and commit tx.config, then reconcile the runtime."""
        new_config = tx.config
        old_config = self._config

        self._repair_config(new_config)
        self._validate_config(new_config)

        changes = diff_config(old_config, new_config)
        effects = calculate_effects(
            changes, old_config, new_config, self.runtime.recording_group_ids()
        )

        self._check_permission(changes)

        self._config = new_config
        self.runtime.runtime_settings = new_config.settings
        self.runtime.runtime_global_placeholder_values = new_config.global_placeholder_values_dict
        self.runtime.runtime_group_placeholder_values = {
            group_id: new_config.group_placeholder_values_dict(group_id)
            for group_id in new_config.all_groups
        }

        self._log_changeset(changes)

        try:
            try:
                self._apply_runtime_changes(changes, effects, old_config, new_config, tx.propagate_duration_group_ids)
            except Exception:
                _logger.error("Runtime reconciliation failed after commit", exc_info=True)
        finally:
            # Config signals are always emitted, even if runtime reconciliation fails.
            self.config_changed.emit(deepcopy(self._config))
            if self._has_persistent_changes(changes):
                self.persistent_config_changed.emit(deepcopy(self._config))
            self._emit_entity_signals(changes)
            self.runtime.refresh_all_group_states()

    # ------------------------------------------------------------------
    # Permission check
    # ------------------------------------------------------------------

    def _check_permission(self, changes: ChangeSet) -> None:
        """Raise if changes are not permitted given the current recording state."""
        changed_sources = [sc for sc, _ in changes.sources_updated.values()]
        changed_sources += list(changes.sources_removed.values())
        for source_config in changed_sources:
            if self.runtime.is_group_recording(source_config.implicit_group_id):
                raise Exception("Cannot edit source while it is used in a recording")

    def _has_persistent_changes(self, changes: ChangeSet) -> bool:
        """Return True if changes affect state that is saved to disk.

        global_placeholder_values_changed is intentionally excluded — placeholder
        values are not currently persisted.  When a "remember me" option is added
        for global placeholders, extend this check accordingly.
        """
        return bool(
            changes.settings_changed
            or changes.sources_added or changes.sources_removed or changes.sources_updated
            or changes.groups_added or changes.groups_removed or changes.groups_updated
            or changes.pipelines_added or changes.pipelines_removed or changes.pipelines_updated
            or changes.placeholders_added or changes.placeholders_removed or changes.placeholders_updated
        )

    # ------------------------------------------------------------------
    # Runtime reconciliation — called by _commit after each config change
    # ------------------------------------------------------------------

    def _log_changeset(self, changes: ChangeSet) -> None:
        """Log a human-readable, field-level summary of what changed in this commit."""
        lines = []

        # ── Settings ───────────────────────────────────────────────────────────
        for key_path, value in changes.settings_changed.items():
            lines.append(f"  setting  {'.'.join(key_path)} = {value!r}")

        # ── Global placeholder values ──────────────────────────────────────────
        for ph_id, (old_val, new_val) in changes.global_placeholder_values_changed.items():
            lines.append(f"  global-placeholder-value  {ph_id!r}: {old_val!r} → {new_val!r}")

        # ── Group placeholder values ───────────────────────────────────────────
        for group_id, ph_changes in changes.group_placeholder_values_changed.items():
            for ph_id, (old_val, new_val) in ph_changes.items():
                lines.append(f"  group-placeholder-value  {group_id!r}/{ph_id!r}: {old_val!r} → {new_val!r}")

        # ── Sources ────────────────────────────────────────────────────────────
        for sc in changes.sources_added.values():
            lines.append(f"  source ADDED    {_fmt_source(sc)}")
        for sc in changes.sources_removed.values():
            lines.append(f"  source REMOVED  name={sc.name!r}  id={sc.id}")
        for old_sc, new_sc in changes.sources_updated.values():
            diff_lines = _flat_diff(old_sc._to_dict_data(), new_sc._to_dict_data())
            if diff_lines:
                lines.append(f"  source UPDATED  name={new_sc.name!r}  id={new_sc.id}")
                lines.extend(f"    {d}" for d in diff_lines)

        # ── Groups ─────────────────────────────────────────────────────────────
        for gc in changes.groups_added.values():
            lines.append(f"  group ADDED    {_fmt_group(gc)}")
        for gc in changes.groups_removed.values():
            lines.append(f"  group REMOVED  name={gc.name!r}  id={gc.id}")
        for old_gc, new_gc in changes.groups_updated.values():
            diff_lines = _flat_diff(old_gc._to_dict_data(), new_gc._to_dict_data())
            if diff_lines:
                lines.append(f"  group UPDATED  name={new_gc.name!r}  id={new_gc.id}")
                lines.extend(f"    {d}" for d in diff_lines)

        # ── Pipelines ──────────────────────────────────────────────────────────
        for pc in changes.pipelines_added.values():
            lines.append(f"  pipeline ADDED    {_fmt_pipeline(pc)}")
        for pc in changes.pipelines_removed.values():
            lines.append(f"  pipeline REMOVED  name={pc.name!r}  id={pc.id}")
        for old_pc, new_pc in changes.pipelines_updated.values():
            diff_lines = _flat_diff(old_pc._to_dict_data(), new_pc._to_dict_data())
            if diff_lines:
                lines.append(f"  pipeline UPDATED  name={new_pc.name!r}  id={new_pc.id}")
                lines.extend(f"    {d}" for d in diff_lines)

        # ── Placeholders ───────────────────────────────────────────────────────
        for pc in changes.placeholders_added.values():
            lines.append(f"  placeholder ADDED    {_fmt_placeholder(pc)}")
        for pc in changes.placeholders_removed.values():
            lines.append(f"  placeholder REMOVED  name={pc.name!r}  id={pc.id}")
        for old_pc, new_pc in changes.placeholders_updated.values():
            diff_lines = _flat_diff(old_pc._to_dict_data(), new_pc._to_dict_data())
            if diff_lines:
                lines.append(f"  placeholder UPDATED  name={new_pc.name!r}  id={new_pc.id}")
                lines.extend(f"    {d}" for d in diff_lines)

        # ── Group ↔ pipeline assignments ──────────────────────────────────────
        for group_id, pipeline_id in changes.group_pipeline_added:
            lines.append(f"  pipeline {pipeline_id!r} ASSIGNED to group {group_id!r}")
        for group_id, pipeline_id in changes.group_pipeline_removed:
            lines.append(f"  pipeline {pipeline_id!r} UNASSIGNED from group {group_id!r}")

        if lines:
            _logger.info("Config committed:\n%s", "\n".join(lines))
        else:
            _logger.debug("Config committed (no structural changes)")

    def _apply_runtime_changes(
        self,
        changes: ChangeSet,
        effects: EffectSet,
        old: AppConfig,
        new: AppConfig,
        propagate_duration_group_ids: Set[str],
    ) -> None:
        """Read the config diff and orchestrate the corresponding runtime operations."""
        rt = self.runtime  # local alias for brevity

        # 0. Stop pipeline previews before any structural teardown.
        for group_id in effects.groups_requiring_preview_stop:
            rt.stop_pipeline_preview(group_id)

        # 1a. Stop source previews for sources being removed or rebuilt.
        for source_id in effects.source_previews_to_stop:
            rt.stop_preview(source_id)

        # 1b. Fully tear down removed sources (source object + widget).
        for source_id in changes.sources_removed:
            rt.teardown_source(source_id)
            rt.teardown_source_widget(source_id)

        # 1c. Tear down source objects that need a rebuild (widget stays).
        for source_id in effects.sources_requiring_rebuild:
            rt.teardown_source(source_id)

        # 2. Tear down groups removed from config.
        for group_id in changes.groups_removed:
            rt.teardown_group(group_id)

        # 3. Create Group objects and controls for newly added groups.
        for group_id in changes.groups_added:
            rt.add_group(group_id)

        # 4. Set up SourceEntry + widget + source for new sources.
        for source_config in changes.sources_added.values():
            rt.setup_source_widget(source_config)
            rt.setup_source(source_config)

        # 5. Sync config-snapshot fields for all known groups.
        for group_id in new.all_groups:
            rt.sync_group_snapshot(group_id, new)

        # 6a. Propagate group-name changes to non-started sessions.
        for group_id, new_name in changes.group_name_changed:
            rt.propagate_group_name(group_id, new_name)

        # 6b. Propagate recording-duration changes to sessions.
        #     Non-started sessions always receive the update.
        #     Running sessions (started but not yet stopping) receive the update
        #     only when the user has explicitly opted in for that group.
        for group_id, (_old_dur, new_dur) in changes.group_recording_duration_changed.items():
            rt.propagate_recording_duration(
                group_id,
                new_dur,
                include_started=(group_id in propagate_duration_group_ids),
            )

        # 6c. Propagate global placeholder-value changes to non-started sessions.
        placeholder_context_changed = bool(
            changes.global_placeholder_values_changed
            or changes.placeholders_added
            or changes.placeholders_removed
            or changes.placeholders_updated
        )
        if placeholder_context_changed:
            rt.propagate_global_placeholder_values(new.global_placeholder_values_dict)

        # 6d. Propagate per-group placeholder-value changes to non-started sessions.
        for group_id in changes.group_placeholder_values_changed:
            rt.propagate_group_placeholder_values(group_id, new.group_placeholder_values_dict(group_id))

        # 7. Ensure every group has an active session.
        for group_id in new.all_groups:
            rt.ensure_active_session(group_id)

        # 8a. Tear down pipelines removed from a group.
        for group_id, pipeline_id in changes.group_pipeline_removed:
            rt.teardown_pipeline(group_id, pipeline_id)

        # 8b. Reconfigure in-place or fully rebuild updated pipelines.
        for group_id, pipeline_id in changes.group_pipeline_updated:
            if pipeline_id not in old.pipelines or pipeline_id not in new.pipelines:
                continue
            if old.pipelines[pipeline_id].pipeline_type == new.pipelines[pipeline_id].pipeline_type:
                rt.configure_pipeline(group_id, pipeline_id)
            else:
                rt.teardown_pipeline(group_id, pipeline_id)
                rt.setup_pipeline(group_id, pipeline_id)

        # 8c. Set up pipelines for newly added groups.
        for group_id in changes.groups_added:
            for pipeline_id in new.all_groups[group_id].pipeline_ids:
                rt.setup_pipeline(group_id, pipeline_id)

        # 8d. Set up pipelines newly assigned to existing groups.
        for group_id, pipeline_id in changes.group_pipeline_added:
            rt.setup_pipeline(group_id, pipeline_id)

        # 9a. Re-create source objects for rebuilt sources.
        for source_config in effects.sources_requiring_rebuild.values():
            rt.setup_source(source_config)

        # 9b. Start previews for sources that need one.
        for source_config in effects.source_previews_to_start.values():
            rt.start_preview(source_config.id)

        # 10. Start pipeline previews for groups that need them.
        for group_id in effects.groups_requiring_preview_start:
            rt.start_pipeline_preview(group_id)

        # Location of recording-controls widgets is determined by the UI layer
        # reacting to active_session_changed (ViewerOnly → hidden, else → bottom).

    # ------------------------------------------------------------------
    # Config repair & validation
    # ------------------------------------------------------------------

    def _repair_config(self, config: AppConfig) -> None:
        self._remove_non_existant_references(config)
        self._update_implicit_groups(config)

    def _remove_non_existant_references(self, config: AppConfig) -> None:
        for source_config in config.sources.values():
            if source_config.group_id is not None and source_config.group_id not in config.groups:
                source_config.group_id = None

        for group_config in config.all_groups.values():
            group_config.pipeline_ids = {
                pcid for pcid in group_config.pipeline_ids if pcid in config.pipelines
            }
            group_sources = {
                sc.id for sc in config.sources.values() if sc.implicit_group_id == group_config.id
            }
            group_config.source_mapping = {
                pid: {
                    input_name: source_id
                    for input_name, source_id in mapping.items()
                    if (
                        input_name in config.pipelines[pid].active_config.inputs
                        and source_id in group_sources
                    )
                }
                for pid, mapping in group_config.source_mapping.items()
                if pid in group_config.pipeline_ids
            }

    def _update_implicit_groups(self, config: AppConfig) -> None:
        for source_id, source_config in config.sources.items():
            if source_config.group_id is None:
                group_name = source_config.name
                if source_id not in config.implicit_groups:
                    config.implicit_groups[source_id] = GroupConfig(
                        id=source_id, name=group_name, implicit=True
                    )
                elif config.implicit_groups[source_id].name != group_name:
                    config.implicit_groups[source_id].name = group_name

        implicit_groups_to_remove = {
            source_id
            for source_id in config.implicit_groups
            if source_id not in config.sources or config.sources[source_id].group_id is not None
        }
        for source_id in implicit_groups_to_remove:
            config.implicit_groups.pop(source_id)

    def _validate_config(self, config: AppConfig) -> None:
        pass

    # ------------------------------------------------------------------
    # Signal emission for config changes
    # ------------------------------------------------------------------

    def _emit_entity_signals(self, changes: ChangeSet) -> None:
        if changes.settings_changed:
            self.settings_changed.emit(deepcopy(changes.settings_changed))

        for gc in changes.groups_added.values():
            self.group_added.emit(deepcopy(gc))
        for _old_gc, new_gc in changes.groups_updated.values():
            self.group_changed.emit(deepcopy(new_gc))
        for gid in changes.groups_removed:
            self.group_removed.emit(gid)

        for sc in changes.sources_added.values():
            self.source_added.emit(deepcopy(sc))
        for _old_sc, new_sc in changes.sources_updated.values():
            self.source_changed.emit(deepcopy(new_sc))
        for sid in changes.sources_removed:
            self.source_removed.emit(sid)

        for pc in changes.pipelines_added.values():
            self.pipeline_added.emit(deepcopy(pc))
        for _old_pc, new_pc in changes.pipelines_updated.values():
            self.pipeline_changed.emit(deepcopy(new_pc))
        for pid in changes.pipelines_removed:
            self.pipeline_removed.emit(pid)

        for placeholder in changes.placeholders_added.values():
            self.placeholder_added.emit(deepcopy(placeholder))
        for _old_p, new_p in changes.placeholders_updated.values():
            self.placeholder_changed.emit(deepcopy(new_p))
        for placeholder_id in changes.placeholders_removed:
            self.placeholder_removed.emit(placeholder_id)

    # ------------------------------------------------------------------
    # Snapshot requests
    # ------------------------------------------------------------------

    @Slot()
    def send_settings_snapshot(self) -> None:
        self.settings_snapshot.emit(deepcopy(self._config.settings))

    @Slot()
    def send_config_snapshot(self) -> None:
        self.config_snapshot.emit(deepcopy(self.config))

    @Slot(str)
    def send_source_snapshot(self, source_id: str) -> None:
        self.source_snapshot.emit(deepcopy(self._config.sources[source_id]))

    @Slot(str)
    def send_group_snapshot(self, group_id: str) -> None:
        self.group_snapshot.emit(deepcopy(self._config.all_groups[group_id]))

    @Slot(str)
    def send_active_session_snapshot(self, group_id: str) -> None:
        self.runtime.send_active_session_snapshot(group_id)

    @Slot()
    def send_group_placeholder_snapshots(self) -> None:
        self.runtime.send_group_placeholder_snapshots()

    # ------------------------------------------------------------------
    # Config CRUD — settings
    # ------------------------------------------------------------------

    @Slot(object)
    def set_settings(self, patch: Dict[Tuple[str, ...], Any]) -> None:
        assert all(isinstance(k, tuple) for k in patch.keys())
        with self.transaction() as tx:
            _logger.info("Settings change: %s", {str(k): v for k, v in patch.items()})
            for key_path, value in patch.items():
                tx.config.settings[key_path] = deepcopy(value)

    # ------------------------------------------------------------------
    # Config CRUD — sources
    # ------------------------------------------------------------------

    @Slot(object)
    def add_source(self, source_config: SourceConfig, reply: Optional[ConfigChangeReply] = None) -> None:
        with self.transaction(reply) as tx:
            assert source_config.id not in tx.config.sources
            tx.config.sources[source_config.id] = source_config

    @Slot(object)
    def edit_source(self, source_config: SourceConfig) -> None:
        with self.transaction() as tx:
            assert source_config.id in tx.config.sources
            tx.config.sources[source_config.id] = source_config

    @Slot(str)
    def remove_source(self, source_id: str) -> None:
        with self.transaction() as tx:
            assert source_id in tx.config.sources
            tx.config.sources.pop(source_id, None)
            tx.config.implicit_groups.pop(source_id, None)

    @Slot(str)
    def setup_source(self, source_id: str) -> None:
        """Re-initialise a source's runtime state from the committed config."""
        source_config = self._config.sources[source_id]
        group_id = source_config.implicit_group_id

        self.runtime.stop_pipeline_preview(group_id)
        self.runtime.stop_preview(source_id)
        self.runtime.teardown_source(source_id)
        self.runtime.setup_source(source_config)
        self.runtime.start_preview(source_id)
        self.runtime.start_pipeline_preview(group_id)
        self.runtime._refresh_group_state(group_id)

    # ------------------------------------------------------------------
    # Config CRUD — groups
    # ------------------------------------------------------------------

    @Slot(object)
    def add_group(self, group_config: GroupConfig) -> None:
        with self.transaction() as tx:
            assert group_config.id not in tx.config.groups
            tx.config.groups[group_config.id] = group_config

    @Slot(object)
    def edit_group(self, group_config: GroupConfig, propagate_duration: bool = False) -> None:
        with self.transaction() as tx:
            assert group_config.id in tx.config.all_groups
            if group_config.id in tx.config.groups:
                tx.config.groups[group_config.id] = group_config
            elif group_config.id in tx.config.implicit_groups:
                tx.config.implicit_groups[group_config.id] = group_config
            if propagate_duration:
                tx.propagate_duration_group_ids.add(group_config.id)

    @Slot(str)
    def remove_group(self, group_id: str) -> None:
        with self.transaction() as tx:
            assert group_id in tx.config.groups
            tx.config.groups.pop(group_id, None)

    @Slot(str, object)
    def assign_group(self, source_id: str, group_id: Optional[str]) -> None:
        with self.transaction() as tx:
            assert source_id in tx.config.sources, f"SourceConfig {source_id} not found"
            assert group_id is None or group_id in tx.config.groups, f"GroupConfig {group_id} not found"
            tx.config.sources[source_id].group_id = group_id

    # ------------------------------------------------------------------
    # Config CRUD — pipelines
    # ------------------------------------------------------------------

    @Slot(object)
    def add_pipeline(self, pipeline_config: PipelineConfig) -> None:
        with self.transaction() as tx:
            assert pipeline_config.id not in tx.config.pipelines
            tx.config.pipelines[pipeline_config.id] = pipeline_config

    @Slot(object)
    def edit_pipeline(self, pipeline_config: PipelineConfig) -> None:
        with self.transaction() as tx:
            assert pipeline_config.id in tx.config.pipelines
            tx.config.pipelines[pipeline_config.id] = pipeline_config

    @Slot(str)
    def remove_pipeline(self, pipeline_id: str) -> None:
        with self.transaction() as tx:
            assert pipeline_id in tx.config.pipelines
            tx.config.pipelines.pop(pipeline_id, None)

    @Slot(str, object)
    def assign_pipeline_to_source(self, source_id: str, pipeline_id: Optional[str]) -> None:
        with self.transaction() as tx:
            assert source_id in tx.config.sources
            assert source_id in tx.config.implicit_groups

            if pipeline_id is None:
                self.set_pipeline_assignment(source_id, set(), {})
                return

            assert pipeline_id in tx.config.pipelines

            source_config = tx.config.sources[source_id]
            pipeline_config = tx.config.pipelines[pipeline_id]

            assert len(pipeline_config.active_config.inputs) == 1
            input_name = pipeline_config.active_config.inputs[0]

            self.set_pipeline_assignment(
                source_id,
                {pipeline_id},
                {pipeline_id: {input_name: source_config.id}},
            )

    @Slot(str, object, object)
    def set_pipeline_assignment(
        self,
        group_id: str,
        pipeline_ids: Set[str],
        source_mapping: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> None:
        with self.transaction() as tx:
            assert group_id in tx.config.all_groups
            assert all(pid in tx.config.pipelines for pid in pipeline_ids)
            group_config = tx.config.all_groups[group_id]
            group_config.pipeline_ids = pipeline_ids
            group_config.source_mapping = source_mapping or {}

    # ------------------------------------------------------------------
    # Config CRUD — placeholders
    # ------------------------------------------------------------------

    @Slot(object)
    def add_placeholder(self, placeholder_config: PlaceholderConfig) -> None:
        with self.transaction() as tx:
            assert placeholder_config.id not in tx.config.placeholders
            tx.config.placeholders[placeholder_config.id] = placeholder_config

    @Slot(object)
    def edit_placeholder(self, placeholder_config: PlaceholderConfig) -> None:
        with self.transaction() as tx:
            assert placeholder_config.id in tx.config.placeholders
            tx.config.placeholders[placeholder_config.id] = placeholder_config

    @Slot(str)
    def remove_placeholder(self, placeholder_id: str) -> None:
        with self.transaction() as tx:
            assert placeholder_id in tx.config.placeholders
            tx.config.placeholders.pop(placeholder_id, None)

    @Slot(list)
    def reorder_placeholders(self, ordered_ids: List[str]) -> None:
        with self.transaction() as tx:
            tx.config.placeholders = OrderedDict(
                (id, tx.config.placeholders[id])
                for id in ordered_ids
                if id in tx.config.placeholders
            )

    @Slot(object, object)
    def update_placeholder_values(self, global_values: Dict[str, str], group_values: Dict[str, Dict[str, str]]) -> None:
        """Merge global and per-group placeholder values into config.

        An empty string is treated as "unset": the key is removed from the
        stored dict so that callers can detect missing values via key absence.
        """
        with self.transaction() as tx:
            for placeholder_id, value in global_values.items():
                if value:
                    tx.config.global_placeholder_values[placeholder_id] = value
                else:
                    tx.config.global_placeholder_values.pop(placeholder_id, None)
            for group_id, values in group_values.items():
                if group_id not in tx.config.group_placeholder_values:
                    tx.config.group_placeholder_values[group_id] = {}
                for placeholder_id, value in values.items():
                    if value:
                        tx.config.group_placeholder_values[group_id][placeholder_id] = value
                    else:
                        tx.config.group_placeholder_values[group_id].pop(placeholder_id, None)

    # ------------------------------------------------------------------
    # Runtime operations — delegated to self.runtime
    # ------------------------------------------------------------------

    @Slot()
    def reconcile_runtime(self) -> None:
        """Reconcile the full runtime state with the committed config."""
        self.runtime.reconcile_runtime(self._config)

    @Slot(str, int)
    def set_recording_number(self, group_id: str, number: int) -> None:
        """Set the recording number of a group to *number*.

        The next session will use ``number + 1``.  Pass ``0`` to effectively
        reset to 1 on the next recording.
        """
        self.runtime.set_recording_number(group_id, number)

    @Slot(str, str)
    def start_recording(self, group_id: str, session_id: str) -> None:
        self.runtime.start_recording(group_id, session_id)
        # If the recording successfully started, clear recording-persistence
        # placeholder values from the config so the user can fill them in for
        # the next session while this recording is still running.
        if self.runtime.is_group_recording(group_id):
            self._clear_recording_persistence_placeholders(group_id)

    def _clear_recording_persistence_placeholders(self, group_id: str) -> None:
        """Remove group-scoped recording-persistence placeholder values from config.

        Called immediately after a recording starts so the UI fields are empty and
        ready for the next session.  The already-started session retains its own
        copy of the values baked into its session object.
        """
        recording_ph_ids = {
            ph_id
            for ph_id, ph in self._config.placeholders.items()
            if ph.persistence == "recording" and not ph.is_global
        }
        if not recording_ph_ids:
            return
        current_group_vals = self._config.group_placeholder_values.get(group_id, {})
        if not any(ph_id in current_group_vals for ph_id in recording_ph_ids):
            return
        with self.transaction() as tx:
            group_vals = tx.config.group_placeholder_values.get(group_id, {})
            for ph_id in recording_ph_ids:
                group_vals.pop(ph_id, None)

    @Slot(str, str)
    def stop_recording(self, group_id: str, session_id: str) -> None:
        self.runtime.stop_recording(group_id, session_id)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @Slot(str, object, bool)
    def save_config(self, config_file: str, ui_state: object, super_user: bool = False) -> None:
        write_protected = False

        if not super_user and os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    write_protected = yaml.safe_load(f).get("write_protected", False)
            except Exception:
                pass

        if write_protected:
            _logger.warning("Save rejected — config file is write-protected: %s", config_file)
            self.error.emit("Config file is write protected. Please save to a different file.", None)
            return

        config_dict = self.config.to_dict()
        with open(config_file, "w+") as f:
            yaml.dump({"write_protected": super_user, "config": config_dict, "ui_state": ui_state}, f)
        _logger.info("Config saved to: %s", config_file)

    @Slot()
    def new_project(self) -> None:
        blank = AppConfig()
        with self.transaction() as tx:
            tx.config.settings = blank.settings
            tx.config.groups = blank.groups
            tx.config.implicit_groups = blank.implicit_groups
            tx.config.sources = blank.sources
            tx.config.pipelines = blank.pipelines
            tx.config.placeholders = blank.placeholders
            tx.config.global_placeholder_values = blank.global_placeholder_values
            tx.config.group_placeholder_values = blank.group_placeholder_values
        self.config_loaded.emit({})

    @Slot(str)
    def load_config(self, config_file: str) -> None:
        _logger.info("Loading config from: %s", config_file)
        with open(config_file, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)

        new_config = AppConfig.from_dict(data["config"], self.config_types)

        with self.transaction() as tx:
            tx.config.settings = new_config.settings
            tx.config.groups = new_config.groups
            tx.config.implicit_groups = new_config.implicit_groups
            tx.config.sources = new_config.sources
            tx.config.pipelines = new_config.pipelines
            tx.config.placeholders = new_config.placeholders
            tx.config.global_placeholder_values = new_config.global_placeholder_values
            tx.config.group_placeholder_values = new_config.group_placeholder_values

        _logger.info("Config loaded successfully from: %s", config_file)
        self.config_loaded.emit(data["ui_state"])
