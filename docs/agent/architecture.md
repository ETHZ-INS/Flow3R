# Architecture Guide

## Layer overview

```
┌─────────────────────────────────────────────┐
│  UI Layer  (src/flow3r/app/widgets/)        │  PySide6 widgets/dialogs
│  read-only consumers of config snapshots    │
└───────────────────┬─────────────────────────┘
                    │ signals / slots only
┌───────────────────▼─────────────────────────┐
│  Controller  (src/flow3r/app/controller/)   │  business logic, no UI
│  Controller · RuntimeController            │
└───────────────────┬─────────────────────────┘
                    │ owns
┌───────────────────▼─────────────────────────┐
│  Config  (src/flow3r/app/config/)           │  frozen @dataclasses
└───────────────────┬─────────────────────────┘
                    │ framework ABCs from
┌───────────────────▼─────────────────────────┐
│  Core  (src/flow3r/core/)                   │  no app knowledge
│  ISource · IPipeline · ConfigBase · …      │
└─────────────────────────────────────────────┘
```

## Controller layer

- `Controller` (a `QObject`) is the **single source of truth** for config state.
- Change config only inside `Controller.transaction()` — never mutate `AppConfig` directly.
- `RuntimeController` manages live source/pipeline/session lifecycle. Do not access it from UI code.
- `WidgetController` bridges controller ↔ UI widgets.

### Signals emitted by `Controller`

| Signal | When emitted |
|---|---|
| `config_snapshot` | Response to `config_snapshot_requested` |
| `config_changed` | Any config mutation |
| `persistent_config_changed` | Mutations that affect the saved `.f3r` file |
| `{entity}_added/changed/removed` | Fine-grained per-entity signals |

## Plugin API

- Plugins are discovered via the `flow3r.plugins` entry-point group.
- `IPlugin.initialize(api)` is called once at startup — register source types, pipeline types, config types, and settings menus here.
- Always call `api.config_types.register(MyConfig.TYPE_ID, MyConfig)` for every config class a plugin introduces — required for `.f3r` deserialisation.
- Public API files that must always carry docstrings are listed in `docs/agent/docs-maintenance.md`.

## Recording groups

- **Explicit groups** live in `AppConfig.groups` — created by the user.
- **Implicit groups** live in `AppConfig.implicit_groups` — auto-created for sources not in any explicit group.
- Do **not** create or remove implicit groups manually; managed by `Controller._update_implicit_groups()`.
- `AppConfig.all_groups` returns `groups | implicit_groups`.

## Placeholder system

- Placeholders are named template variables injected into file paths and session metadata.
- `PlaceholderConfig.is_global=True` → global dialog; `False` → group-scoped.
- `persistence` values: `"session"` (forgotten on restart) · `"project"` (saved to `.f3r`) · `"recording"` (reset after each recording).
- `is_constant=True` is only valid when `is_global=True` and `persistence="project"`.
- `AppConfig.global_placeholder_values_dict` returns the resolved `name → value` dict.

