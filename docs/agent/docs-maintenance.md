# Documentation Maintenance Guide

Treat docs as part of the code. Update them in the same change — not afterwards.

## Document map

| Location | Audience | Update when |
|---|---|---|
| `README.md` | GitHub visitors | Feature additions, install changes, renamed entry points |
| `CHANGELOG.md` | Users upgrading | Every user-visible change, every config schema version bump |
| `CONTRIBUTING.md` | Contributors | Dev workflow changes, new conventions, new tooling |
| `docs/user-guide/` | Lab researchers | New UI features, changed workflows, new source/pipeline types |
| `docs/plugin-dev/` | Plugin authors | Changes to `IPlugin`, `IPluginAPI`, `SourceType`, `PipelineType`, registration |
| `docs/architecture/` | Contributors | Config layer, controller signals, UI patterns, recording groups |
| `docs/api-reference/` | Plugin authors | Auto-generated — kept current by updating docstrings |
| Docstrings (list below) | Plugin authors | Whenever the public API class or method changes |

## Public API files — docstrings required on every class and public method

- `src/flow3r/core/plugin/plugin.py` — `IPlugin`
- `src/flow3r/core/api/plugins/plugins.py` — `IPluginAPI`
- `src/flow3r/app/api/plugins/plugins.py` — `PluginAPI`
- `src/flow3r/app/api/plugins/source_type_registry.py` — `SourceTypeRegistry`
- `src/flow3r/app/api/plugins/pipeline_type_registry.py` — `PipelineTypeRegistry`
- `src/flow3r/core/source/abc/source_type.py` — `ISourceType`, `SourceType`
- `src/flow3r/core/pipeline/abc/pipeline_type.py` — `IPipelineType`, `PipelineType`
- `src/flow3r/core/source/abc/source.py` — `ISource`
- `src/flow3r/core/pipeline/abc/pipeline.py` — `IPipeline`, `PipelineBase`, `PipelineSubscription`, `PreviewSubscription`
- `src/flow3r/core/config/abc/config.py` — `ConfigBase`
- `src/flow3r/core/source/abc/source_config.py` — `SourceConfigBase`
- `src/flow3r/core/pipeline/abc/pipeline_config.py` — `PipelineConfigBase`, `IPipelineConfig`

## Decision rules

### Adding a new source or pipeline type
- Update `docs/user-guide/index.md` — add to the relevant table.
- Add docstrings to any new public API classes.
- Update `docs/plugin-dev/index.md` if the registration pattern changes.
- Add a `CHANGELOG.md` entry only if it's a user-visible built-in.

### Changing `IPlugin`, `IPluginAPI`, `SourceType`, `PipelineType`, or any registration API
- Update docstrings on the affected file immediately.
- Update `docs/plugin-dev/index.md` and the worked example if signatures change.
- Add a `CHANGELOG.md` entry — this is a breaking or additive API change.

### Adding or changing a config field
- Public API config (`SourceConfigBase`, `PipelineConfigBase`): update docstring and `docs/plugin-dev/index.md`.
- `VERSION` incremented: add a `CHANGELOG.md` entry with class name and old/new VERSION.
- Internal app config (`AppConfig`, `GroupConfig`): `CHANGELOG.md` entry only if `.f3r` format changes.

### Adding a new UI dialog or widget
- Update `docs/user-guide/index.md` if it adds a user-visible workflow step.
- Update `docs/architecture/index.md` if it introduces a new pattern.
- No docstrings required on internal widget classes.

### Changing the controller, session lifecycle, or signal/slot patterns
- Update `docs/architecture/index.md`.
- If it affects plugin/session interaction, update `docs/plugin-dev/index.md` and docstrings.

### Breaking change to `.f3r` file format
- Add a `CHANGELOG.md` entry with the config class name and old/new `VERSION`.
- Update `docs/user-guide/index.md` if users need to re-save project files.

## `CHANGELOG.md` format

```markdown
## [x.y.z] — YYYY-MM-DD

### Added
- ...

### Changed
- `RecordVideoConfig` schema bumped to VERSION 2; existing `.f3r` files are migrated automatically.

### Fixed
- ...
```

## Verifying the docs build

```powershell
conda run -n GrimaceRecorder mkdocs build --strict
```

`--strict` promotes warnings (broken links, missing docstrings) to errors. Fix all before finishing.

