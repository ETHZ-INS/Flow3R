# Config Layer Guide

## Overview

All configuration is modelled as **frozen-at-runtime `@dataclass`** objects inheriting from `ConfigBase`.

- `ConfigBase` provides `to_dict()` / `from_dict()` serialisation via `_to_dict_data()` / `_from_dict_data()`.
- Every config class has a `VERSION` class variable.
- IDs are `uuid.uuid4()` strings generated at dataclass construction time.

## Adding a new config field

1. Add the field with a **default value** to the `@dataclass`.
2. Include it in `_to_dict_data()`.
3. Load it with `data.get("field", default)` in `_from_dict_data()` — **never** `data["field"]`.
4. If it belongs to `AppConfig`, ensure `AppConfig._to_dict_data()` includes it.

## Breaking schema changes

1. Increment `VERSION` on the affected config class.
2. Implement `_migrate_data(cls, data, from_version)` to handle older saved data.
3. Add a `CHANGELOG.md` entry — see `docs/agent/docs-maintenance.md`.

## Config error handling

Raise these exceptions from `flow3r.core.config.abc.config`:

| Exception | When |
|---|---|
| `ConfigError` | General serialisation failure |
| `ConfigVersionError` | Unrecognised version number |
| `ConfigTypeMismatchError` | Unexpected type in deserialized data |

## Key config classes

| Class | File | Purpose |
|---|---|---|
| `AppConfig` | `app/config/app_config.py` | Top-level config; owns all sub-configs |
| `GroupConfig` | `app/config/group_config.py` | One recording group |
| `SourceConfigBase` | `core/source/abc/source_config.py` | Base for all source configs |
| `PipelineConfigBase` | `core/pipeline/abc/pipeline_config.py` | Base for all pipeline configs |
| `PlaceholderConfig` | `app/config/placeholder_config.py` | One placeholder definition |
| `RecordingConfig` | `app/config/recording_config.py` | Recording timing/path settings |

