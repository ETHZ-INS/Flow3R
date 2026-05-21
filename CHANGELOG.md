# Changelog

All notable changes to Flow3R are documented here. This project uses [Semantic Versioning](https://semver.org/).

Config schema versions are noted where relevant — old `.f3r` project files are automatically migrated on load unless otherwise stated.

---

## [0.3.0] — 2026-05-21

### Added
- Plugin API (`IPlugin`, `IPluginAPI`) allowing external packages to register source types, pipeline types, visualizers, and settings panels via the `flow3r.plugins` entry-point group.
- Core plugin providing: Webcam, Pylon Camera, Video File, Audio File, and Microphone source types; Record Video, Record Audio, and Record Video with Audio pipeline types.
- Placeholder system: named template variables injected into file paths and session metadata, with `session`, `project`, and `recording` persistence levels.
- Recording groups (explicit and implicit) with independent recording controls, timing, and pipeline assignment.
- Save/load full project configuration as `.f3r` YAML files.
- Per-session logging to `%LOCALAPPDATA%\ETH3RHub\Flow3R\logs\`.

## [0.4.0] — 2026-05-21

### Added
- `IterativePipeline` base class (`flow3r.core.pipeline.iterative_pipeline`) — lets pipeline authors write a plain blocking `run(sources: Dict[str, Iterable])` method instead of working with RxPY observables directly.  The framework runs `run()` on a background thread, bridges each source stream into a Python iterator, and signals completion automatically.

### Changed
- **Breaking:** `IPipeline.build()` signature changed.  The method now receives a `PipelineContext` as its first argument instead of `session_context`, and returns `None` instead of a `PipelineSubscription`.  Migrate existing implementations by replacing `return PipelineSubscription(disposable, primary_done)` with `context.register_primary_done(primary_done); context.add_disposable(disposable)`.
- `PipelineContext` added to `flow3r.core.pipeline.abc.pipeline` — carries `session_context`, the new `control` observable, and registration methods (`register_primary_done`, `register_secondary_done`, `register_progress`, `add_disposable`).
- Recording lifecycle: a `control` observable is now available on every `Recording` object; it emits `None` when the gate opens and completes when stop is requested.
