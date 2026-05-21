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

