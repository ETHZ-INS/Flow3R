"""
Runtime model for the controller.

These dataclasses hold the *live* state of every source, group, and session.
They are the single source of truth for all runtime operations
(preview, recording, session-state calculation).  The controller is
responsible for keeping them in sync with the committed AppConfig; no
runtime operation should read from the config directly.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from reactivex import Subject
from reactivex.abc import DisposableBase

from flow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription, PreviewSubscription
from flow3r.core.pipeline.abc.pipeline_config import IPipelineConfig
from flow3r.core.source.abc.source import ISource
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

@dataclass
class SourceEntry:
    """Runtime state for a single source."""

    name: str = ""
    group_id: str = ""
    source: Optional[ISource] = None
    widget_handle: Optional[IVisualizerHandle] = None
    preview_sub: Optional[DisposableBase] = None
    setup_error: Optional[str] = None
    preview_error: Optional[str] = None


# ---------------------------------------------------------------------------
# Preview / Recording
# ---------------------------------------------------------------------------

@dataclass
class Preview:
    """Active pipeline-preview subscription for a group."""

    connections: List[DisposableBase]
    preview_sub: Optional[PreviewSubscription]


@dataclass
class Recording:
    """Active recording subscription for a session."""

    start: Subject
    stop: Subject
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    acquisition_finished_time: Optional[datetime] = None
    processing_finished_time: Optional[datetime] = None
    connections: Optional[List[DisposableBase]] = None
    pipeline_sub: Optional[PipelineSubscription] = None
    primary_finished: bool = False
    secondary_finished: bool = False
    finished: bool = False
    progress: Tuple[int, int] = (0, 0)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@dataclass
class Session:
    """Runtime state for a single recording session.

    All information required to calculate the session state and to start a
    recording is stored here.  The controller copies the relevant pieces of
    the committed AppConfig into these fields so that runtime operations never
    need to reach back into the config.
    """

    group_id: str
    session_id: str
    group_name: str
    recording_number: int

    # ---- config snapshots (written by the controller, read by runtime ops) ----

    # Snapshot of AppConfig.global_placeholder_values_dict at the time the
    # session was (last) refreshed.  Updated for non-started sessions whenever
    # the resolved global placeholder values change.
    global_placeholder_values: Dict[str, str] = field(default_factory=dict)

    # ---- mutable fields kept in sync before a recording starts ----

    recording_duration: Optional[float] = None

    # ---- set at session creation, frozen once recording starts ----

    # ---- written during recording ----

    recording: Optional[Recording] = None
    start_error: Optional[str] = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_placeholder_values(self) -> Dict[str, Any]:
        """Return all placeholder substitution values for this session.

        Merges global placeholder values with per-session values.
        Uses the recording's actual start time if the recording has started,
        otherwise falls back to datetime.now() as an approximation (used when
        previewing output file paths before recording begins).
        """
        start_time = (
            self.recording.start_time
            if self.recording is not None and self.recording.start_time is not None
            else datetime.now()
        )
        return self.global_placeholder_values | {
            "group_name": self.group_name,
            "recording_number": str(self.recording_number),
            "recording_start_time": start_time.strftime("%Y-%m-%dT%H-%M-%S"),
        }


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------

@dataclass
class Group:
    """Runtime state for a single group (a set of sources + pipelines).

    Pipeline and source information is snapshotted from the AppConfig by the
    controller so that runtime operations (preview, recording, session-state
    calculation) can work entirely from this object without touching the config.
    """

    group_id: str
    group_name: str

    # ---- sessions ----

    sessions: Dict[str, "Session"] = field(default_factory=dict)
    next_recording_number: int = 1
    active_session_id: Optional[str] = None

    # ---- config snapshots (written by the controller, read by runtime ops) ----

    # Ordered list of pipeline IDs assigned to this group.
    # Snapshot of group_config.pipeline_ids.
    pipeline_ids: List[str] = field(default_factory=list)

    # Pipeline display names, keyed by pipeline ID.
    # Snapshot of config.pipelines[pid].name for each pipeline in pipeline_ids.
    pipeline_names: Dict[str, str] = field(default_factory=dict)

    # Pipeline type identifiers, keyed by pipeline ID.
    # Snapshot of config.pipelines[pid].pipeline_type for each pipeline in pipeline_ids.
    # Used by _setup_pipeline to instantiate the correct factory.
    pipeline_type_ids: Dict[str, str] = field(default_factory=dict)

    # Active (unresolved) pipeline configs, keyed by pipeline ID.
    # Snapshot of config.pipelines[pid].active_config for each pipeline in pipeline_ids.
    # Used by session-state calculation to resolve placeholder templates and
    # derive the list of output files.
    pipeline_active_configs: Dict[str, IPipelineConfig] = field(default_factory=dict)

    # Input name lists, keyed by pipeline ID.
    # Snapshot of config.pipelines[pid].active_config.inputs.
    pipeline_input_names: Dict[str, List[str]] = field(default_factory=dict)

    # Source mapping: pipeline_id → {input_name → source_id}.
    # Snapshot of group_config.source_mapping.
    source_mapping: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # Ordered list of source IDs that belong to this group.
    source_ids: List[str] = field(default_factory=list)

    # Names of all non-constant user-defined placeholders that must have a
    # value before recording can start.  Snapshot of config.placeholders,
    # kept up to date by sync_group_snapshot on every commit.
    required_placeholder_names: List[str] = field(default_factory=list)

    # ---- mutable fields kept in sync from config ----

    recording_duration: Optional[float] = None

    # ---- live pipeline instances (populated by setup/teardown helpers) ----

    pipelines: Dict[str, IPipeline] = field(default_factory=dict)

    # ---- error state ----

    runtime_error: Optional[str] = None
    # pipeline_id → error message for pipelines that failed to set up or configure
    pipeline_errors: Dict[str, str] = field(default_factory=dict)
    preview_error: Optional[str] = None

    # ---- widget / UI state ----

    controls_initialized: bool = False

    # ---- active preview subscription ----

    preview: Optional[Preview] = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def active_session(self) -> Optional[Session]:
        return self.sessions[self.active_session_id] if self.active_session_id else None

    def new_session(self, active: bool = True) -> str:
        """Create and register a new session, returning its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(
            group_id=self.group_id,
            session_id=session_id,
            group_name=self.group_name,
            recording_number=self.next_recording_number,
            recording_duration=self.recording_duration,
        )
        self.next_recording_number += 1
        if active:
            self.active_session_id = session_id
        return session_id
