from dataclasses import dataclass
from typing import Dict, Any, Tuple, List, Set, Optional

from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.group_config import GroupConfig
from flow3r.app.config.pipeline_config import PipelineConfig
from flow3r.app.config.placeholder_config import PlaceholderConfig
from flow3r.app.config.source_config import SourceConfig


@dataclass(frozen=True)
class ChangeSet:
    settings_changed: Dict[Tuple[str, ...], Any]
    global_placeholder_values_changed: Dict[str, Tuple[Optional[str], Optional[str]]]

    groups_added: Dict[str, GroupConfig]
    groups_removed: Dict[str, GroupConfig]
    groups_updated: Dict[str, Tuple[GroupConfig, GroupConfig]]

    sources_added: Dict[str, SourceConfig]
    sources_removed: Dict[str, SourceConfig]
    sources_updated: Dict[str, Tuple[SourceConfig, SourceConfig]]

    pipelines_added: Dict[str, PipelineConfig]
    pipelines_removed: Dict[str, PipelineConfig]
    pipelines_updated: Dict[str, Tuple[PipelineConfig, PipelineConfig]]

    placeholders_added: Dict[str, PlaceholderConfig]
    placeholders_removed: Dict[str, PlaceholderConfig]
    placeholders_updated: Dict[str, Tuple[PlaceholderConfig, PlaceholderConfig]]

    source_name_changed: List[Tuple[str, str]]
    source_group_changed: List[Tuple[str, Optional[str], Optional[str]]]

    group_name_changed: List[Tuple[str, str]]
    group_pipeline_added: Set[Tuple[str, str]]
    group_pipeline_removed: Set[Tuple[str, str]]
    group_pipeline_updated: Set[Tuple[str, str]]
    group_recording_duration_changed: Dict[str, Tuple[Optional[float], Optional[float]]]
    group_placeholder_values_changed: Dict[str, Dict[str, Tuple[Optional[str], Optional[str]]]]


@dataclass(frozen=True)
class EffectSet:
    sources_requiring_rebuild: Dict[str, SourceConfig]
    source_previews_to_stop: Set[str]
    source_previews_to_start: Dict[str, SourceConfig]

    groups_requiring_session_state_refresh: Set[str]
    groups_requiring_preview_stop: Set[str]
    groups_requiring_preview_start: Set[str]

    impacted_group_ids: Set[str]


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


def diff_config(old: AppConfig, new: AppConfig) -> ChangeSet:
    settings_changed = {k: v for k, v in new.settings.items() if old.settings.get(k) != v}
    global_placeholder_values_changed = {
        placeholder_id: (old.global_placeholder_values.get(placeholder_id), new.global_placeholder_values.get(placeholder_id))
        for placeholder_id in set(old.global_placeholder_values) | set(new.global_placeholder_values)
        if old.global_placeholder_values.get(placeholder_id) != new.global_placeholder_values.get(placeholder_id)
    }

    groups_added, groups_removed, groups_updated = diff_by_id(old.all_groups, new.all_groups)
    sources_added, sources_removed, sources_updated = diff_by_id(old.sources, new.sources)
    pipelines_added, pipelines_removed, pipelines_updated = diff_by_id(old.pipelines, new.pipelines)
    placeholders_added, placeholders_removed, placeholders_updated = diff_by_id(old.placeholders, new.placeholders)

    for pipeline_config in new.pipelines.values():
        if pipeline_config.id not in old.pipelines:
            continue

        settings_dependencies = pipeline_config.active_config.settings_dependencies
        if any(dep in settings_changed for dep in settings_dependencies):
            pipelines_updated[pipeline_config.id] = (old.pipelines[pipeline_config.id], pipeline_config)

    source_name_changed: List[Tuple[str, str]] = []
    source_group_changed: List[Tuple[str, Optional[str], Optional[str]]] = []
    for old_sc, new_sc in sources_updated.values():
        if old_sc.name != new_sc.name:
            source_name_changed.append((new_sc.id, new_sc.name))
        if old_sc.group_id != new_sc.group_id:
            source_group_changed.append((new_sc.id, old_sc.group_id, new_sc.group_id))

    group_name_changed: List[Tuple[str, str]] = []
    group_pipeline_added: Set[Tuple[str, str]] = set()
    group_pipeline_removed: Set[Tuple[str, str]] = set()
    group_pipeline_updated: Set[Tuple[str, str]] = set()
    group_recording_duration_changed: Dict[str, Tuple[Optional[float], Optional[float]]] = {}

    for group_config in groups_added.values():
        new_duration = group_config.recording_config.recording_duration if group_config.recording_config.recording_mode == "timed" else None
        group_recording_duration_changed[group_config.id] = (None, new_duration)

    for old_gc, new_gc in groups_updated.values():
        if old_gc.name != new_gc.name:
            group_name_changed.append((new_gc.id, new_gc.name))

        for pipeline_id in new_gc.pipeline_ids:
            if pipeline_id not in old_gc.pipeline_ids:
                group_pipeline_added.add((new_gc.id, pipeline_id))
        for pipeline_id in old_gc.pipeline_ids:
            if pipeline_id not in new_gc.pipeline_ids:
                group_pipeline_removed.add((new_gc.id, pipeline_id))

        old_duration = old_gc.recording_config.recording_duration if old_gc.recording_config.recording_mode == "timed" else None
        new_duration = new_gc.recording_config.recording_duration if new_gc.recording_config.recording_mode == "timed" else None
        if old_duration != new_duration:
            group_recording_duration_changed[new_gc.id] = (old_duration, new_duration)

    for group_config in new.all_groups.values():
        old_group_config = old.all_groups.get(group_config.id)
        if old_group_config is None:
            continue
        for pipeline_id in group_config.pipeline_ids:
            if pipeline_id in old_group_config.pipeline_ids and pipeline_id in pipelines_updated:
                group_pipeline_updated.add((group_config.id, pipeline_id))

    group_placeholder_values_changed: Dict[str, Dict[str, Tuple[Optional[str], Optional[str]]]] = {}
    for group_id in set(old.group_placeholder_values) | set(new.group_placeholder_values):
        old_vals = old.group_placeholder_values.get(group_id, {})
        new_vals = new.group_placeholder_values.get(group_id, {})
        changed_phs = {
            placeholder_id: (old_vals.get(placeholder_id), new_vals.get(placeholder_id))
            for placeholder_id in set(old_vals) | set(new_vals)
            if old_vals.get(placeholder_id) != new_vals.get(placeholder_id)
        }
        if changed_phs:
            group_placeholder_values_changed[group_id] = changed_phs

    return ChangeSet(
        settings_changed=settings_changed,
        global_placeholder_values_changed=global_placeholder_values_changed,
        groups_added=groups_added,
        groups_removed=groups_removed,
        groups_updated=groups_updated,
        sources_added=sources_added,
        sources_removed=sources_removed,
        sources_updated=sources_updated,
        pipelines_added=pipelines_added,
        pipelines_removed=pipelines_removed,
        pipelines_updated=pipelines_updated,
        placeholders_added=placeholders_added,
        placeholders_removed=placeholders_removed,
        placeholders_updated=placeholders_updated,
        source_name_changed=source_name_changed,
        source_group_changed=source_group_changed,
        group_name_changed=group_name_changed,
        group_pipeline_added=group_pipeline_added,
        group_pipeline_removed=group_pipeline_removed,
        group_pipeline_updated=group_pipeline_updated,
        group_recording_duration_changed=group_recording_duration_changed,
        group_placeholder_values_changed=group_placeholder_values_changed,
    )


def _group_source_ids(config: AppConfig, group_id: str) -> Set[str]:
    return {source_config.id for source_config in config.sources.values() if source_config.implicit_group_id == group_id}


def source_requires_rebuild(old_source_config: SourceConfig, new_source_config: SourceConfig) -> bool:
    return old_source_config.active_config != new_source_config.active_config


def sources_requiring_rebuild(changes: ChangeSet) -> Dict[str, SourceConfig]:
    return {
        new_source_config.id: new_source_config
        for old_source_config, new_source_config in changes.sources_updated.values()
        if source_requires_rebuild(old_source_config, new_source_config)
    }


def _placeholder_context_changed(changes: ChangeSet) -> bool:
    return bool(
        changes.placeholders_added
        or changes.placeholders_removed
        or changes.placeholders_updated
        or changes.global_placeholder_values_changed
        or changes.group_placeholder_values_changed
    )


def group_ids_with_pipeline_updates(changes: ChangeSet) -> Set[str]:
    return {group_id for group_id, _pipeline_id in changes.group_pipeline_updated}


def group_requires_session_state_refresh(changes: ChangeSet, group_id: str) -> bool:
    return bool(
        _placeholder_context_changed(changes)
        or any(group_id == changed_group_id for changed_group_id, _group_name in changes.group_name_changed)
        or any(group_id == changed_group_id for changed_group_id, _pipeline_id in changes.group_pipeline_added)
        or any(group_id == changed_group_id for changed_group_id, _pipeline_id in changes.group_pipeline_removed)
        or any(group_id == changed_group_id for changed_group_id, _pipeline_id in changes.group_pipeline_updated)
    )


def group_requires_preview_context_refresh(changes: ChangeSet, group_id: str) -> bool:
    return bool(
        _placeholder_context_changed(changes)
        or any(group_id == changed_group_id for changed_group_id, _group_name in changes.group_name_changed)
    )


def group_requires_preview_restart(
    changes: ChangeSet,
    old: AppConfig,
    new: AppConfig,
    group_id: str,
    rebuilt_source_ids: Set[str],
) -> bool:
    if group_id in changes.groups_added:
        return False

    if group_requires_preview_context_refresh(changes, group_id) or group_id in group_ids_with_pipeline_updates(changes):
        return True

    old_group_config = old.all_groups[group_id]
    new_group_config = new.all_groups[group_id]
    old_source_ids = _group_source_ids(old, group_id)
    new_source_ids = _group_source_ids(new, group_id)
    affected_source_ids = old_source_ids | new_source_ids

    return bool(
        old_group_config.pipeline_ids != new_group_config.pipeline_ids
        or old_group_config.source_mapping != new_group_config.source_mapping
        or old_source_ids != new_source_ids
        or bool(affected_source_ids & rebuilt_source_ids)
    )


def group_requires_preview_start(changes: ChangeSet, group_id: str) -> bool:
    return group_id in changes.groups_added


def impacted_group_ids(
    changes: ChangeSet,
    groups_requiring_session_state_refresh: Set[str],
    groups_requiring_preview_stop: Set[str],
    groups_requiring_preview_start: Set[str],
) -> Set[str]:
    group_ids = set(changes.groups_added) | set(changes.groups_removed)
    group_ids |= groups_requiring_session_state_refresh
    group_ids |= groups_requiring_preview_stop
    group_ids |= groups_requiring_preview_start
    group_ids |= {source_config.implicit_group_id for source_config in changes.sources_added.values()}
    group_ids |= {source_config.implicit_group_id for source_config in changes.sources_removed.values()}
    group_ids |= {old_source_config.implicit_group_id for old_source_config, _ in changes.sources_updated.values()}
    group_ids |= {new_source_config.implicit_group_id for _, new_source_config in changes.sources_updated.values()}
    return group_ids


def calculate_effects(
    changes: ChangeSet,
    old: AppConfig,
    new: AppConfig,
    recording_group_ids: Optional[Set[str]] = None,
) -> EffectSet:
    recording_group_ids = recording_group_ids or set()

    rebuilt_sources = sources_requiring_rebuild(changes)
    rebuilt_source_ids = set(rebuilt_sources)

    groups_requiring_session_state_refresh = {
        group_id
        for group_id in new.all_groups
        if group_requires_session_state_refresh(changes, group_id)
    }

    groups_requiring_preview_stop = set(changes.groups_removed)
    groups_requiring_preview_start = set()

    for group_id in new.all_groups:
        if group_id in recording_group_ids:
            continue

        if group_requires_preview_start(changes, group_id):
            groups_requiring_preview_start.add(group_id)
            continue

        if group_requires_preview_restart(changes, old, new, group_id, rebuilt_source_ids):
            groups_requiring_preview_stop.add(group_id)
            groups_requiring_preview_start.add(group_id)

    source_previews_to_stop = set(changes.sources_removed) | set(rebuilt_sources)
    source_previews_to_start = rebuilt_sources | changes.sources_added

    return EffectSet(
        sources_requiring_rebuild=rebuilt_sources,
        source_previews_to_stop=source_previews_to_stop,
        source_previews_to_start=source_previews_to_start,
        groups_requiring_session_state_refresh=groups_requiring_session_state_refresh,
        groups_requiring_preview_stop=groups_requiring_preview_stop,
        groups_requiring_preview_start=groups_requiring_preview_start,
        impacted_group_ids=impacted_group_ids(
            changes,
            groups_requiring_session_state_refresh,
            groups_requiring_preview_stop,
            groups_requiring_preview_start,
        ),
    )
