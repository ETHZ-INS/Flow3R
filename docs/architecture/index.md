# Architecture

This page describes the internal design of Flow3R for contributors.  End users and plugin authors can skip this.

---

## Layer overview

```
┌─────────────────────────────────────────────┐
│  UI Layer  (flow3r/app/widgets/)            │  PySide6 widgets, dialogs
│  read-only consumers of config snapshots    │
└───────────────────┬─────────────────────────┘
                    │ signals / slots
┌───────────────────▼─────────────────────────┐
│  Controller Layer  (flow3r/app/controller/) │  business logic, no UI
│  Controller · RuntimeController            │
└───────────────────┬─────────────────────────┘
                    │ owns
┌───────────────────▼─────────────────────────┐
│  Config Layer  (flow3r/app/config/)         │  pure-data frozen @dataclasses
│  AppConfig · GroupConfig · SourceConfig … │
└─────────────────────────────────────────────┘
        ▲  framework ABCs from
┌───────┴──────────────────────────────────────┐
│  Core  (flow3r/core/)                        │  no app knowledge
│  ISource · IPipeline · ConfigBase · …       │
└──────────────────────────────────────────────┘
```

---

## Config layer (`flow3r/app/config/`)

All configuration is modelled as **frozen-at-runtime `@dataclass`** objects inheriting from `ConfigBase`.

- `ConfigBase` provides `to_dict()` / `from_dict()` serialisation via `_to_dict_data()` / `_from_dict_data()`.
- Every config class has a `VERSION` class variable.  Increment it and implement `_migrate_data()` when making breaking schema changes.
- **New fields must always have a default value** and be loaded with `.get('field', default)` in `_from_dict_data` to maintain backwards compatibility with existing `.f3r` files.
- IDs are `uuid.uuid4()` strings generated at dataclass construction time.

---

## Controller layer (`flow3r/app/controller/`)

`Controller` (a `QObject`) is the **single source of truth** for configuration state.

- It owns `self._config: AppConfig` (the committed config).  Never mutate it directly from outside.
- All config changes go through `Controller.transaction()`: a context manager that yields a mutable draft, diffs it against the committed state on exit, and emits the appropriate signals.
- `RuntimeController` handles live source/pipeline/session lifecycle.  It is owned by `Controller` and should not be accessed from UI code.

Config signals emitted by `Controller`:

| Signal | When |
|---|---|
| `config_snapshot` | Response to `config_snapshot_requested` |
| `config_changed` | Any config mutation |
| `persistent_config_changed` | Config changes that affect the saved `.f3r` file |
| `{entity}_added/changed/removed` | Fine-grained per-entity signals |

---

## UI layer (`flow3r/app/widgets/`)

- Each dialog/widget is a hand-written class.  Layout is defined in `ui/` XML and compiled to `layout/` Python by `pyside6-uic`.
- Widget classes use **multiple inheritance**: `class MyDialog(Ui_MyDialog, QDialog)`.
- Widgets are **read-only consumers** of config snapshots.  They must never write to `AppConfig` directly; they signal changes through the controller.
- Use the `config_snapshot_requested` → `controller.send_config_snapshot()` pattern to request an initial snapshot in `__init__`.

---

## Recording groups

- **Explicit groups** live in `AppConfig.groups` and are created by the user.
- **Implicit groups** in `AppConfig.implicit_groups` are auto-created for sources not assigned to an explicit group.  They are managed automatically by `Controller._update_implicit_groups()` — do not create or remove them manually.
- `AppConfig.all_groups` returns `groups | implicit_groups`.

---

## Placeholder system

Placeholders are named template variables injected into file paths and session metadata.

| Field | Allowed values | Meaning |
|---|---|---|
| `persistence` | `"session"` | Forgotten on application restart |
| `persistence` | `"project"` | Saved to the `.f3r` file |
| `persistence` | `"recording"` | Reset after each recording |
| `is_global` | `True` | Shown in global placeholders dialog |
| `is_constant` | `True` | Only valid when `is_global=True` and `persistence="project"` |

---

## Key conventions

| Topic | Rule |
|---|---|
| `blockSignals` | Required around programmatic `setChecked` / `setCurrentIndex` / etc. to prevent re-entrant handlers |
| `QMessageBox` | Write config state *before* calling `exec()` — modal dialogs spin the Qt event loop |
| `@Slot(...)` | Decorate all slot methods in `QObject` subclasses |
| Logging | Use `get_logger(__name__)` from `flow3r.logger` |
| Config errors | Raise `ConfigError` from `flow3r.core.config.abc.config` |

---

## `.ui` file workflow

Layout files in `src/flow3r/app/layout/` are auto-generated from Qt Designer XML in `src/flow3r/app/ui/`.  **Never edit `layout/` files by hand.**

```bash
# recompile all at once:
src\flow3r\app\compile_ui.bat

# or a single file:
pyside6-uic "src/flow3r/app/ui/MyDialog.ui" -o "src/flow3r/app/layout/my_dialog.py"
```

