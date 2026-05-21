# Contributing to Flow3R

Thank you for your interest in contributing! This guide covers everything you need to get a working dev environment and make changes confidently.

---

## Dev environment

Flow3R uses **[uv](https://docs.astral.sh/uv/)** for environment and dependency management.

```bash
# Install all dependencies (creates .venv automatically)
uv sync --extra dev

# Run any command inside the managed environment
uv run python src/main.py
```

All Python commands in this project must be prefixed with `uv run` if the virtual environment is not already activated.

---

## Repository layout

```
src/flow3r/
├── app/
│   ├── config/       # Pure-data config dataclasses (@dataclass, frozen at runtime)
│   ├── controller/   # Business logic — config CRUD, live session lifecycle
│   ├── ui/           # Qt Designer XML source files (*.ui) — EDIT THESE
│   ├── layout/       # AUTO-GENERATED Python from *.ui — DO NOT EDIT BY HAND
│   ├── widgets/      # Hand-written PySide6 widget/dialog classes
│   └── api/          # Plugin and service API exposed to external plugins
├── core/             # Framework-level abstractions (no app knowledge)
│   ├── config/abc/   # ConfigBase, IConfig, ITypedConfig
│   ├── source/abc/   # ISource, ISourceType, SourceConfigBase
│   ├── pipeline/abc/ # IPipeline, PipelineBase, IPipelineType, PipelineConfigBase
│   └── streaming/    # Frame buffer, decode threads
└── plugins/          # First-party plugin implementations
    └── core/         # Built-in sources (webcam, Pylon, …) and pipelines (record …)
```

---

## Compiling UI files

Layout files in `src/flow3r/app/layout/` are auto-generated from Qt Designer XML files in `src/flow3r/app/ui/`. **Never edit `layout/` files by hand** — they are overwritten whenever you recompile.

```bash
# Recompile all UI files at once (from repo root):
uv run src\flow3r\app\compile_ui.bat

# Or compile a single file:
uv run pyside6-uic "src/flow3r/app/ui/MyDialog.ui" -o "src/flow3r/app/layout/my_dialog.py"
```

> **Gotcha:** Use PowerShell `[System.IO.File]::WriteAllText(...)` when editing `.ui` files programmatically. The standard file-edit tools may silently fail due to whitespace mismatches.

---

## Adding a config field

1. Add the field with a **default value** to the `@dataclass` in `app/config/`.
2. Add it to `_to_dict_data()`.
3. Load it with `.get('field', default)` — never bare `data['field']` — in `_from_dict_data()`. This keeps backwards compatibility with existing `.f3r` project files.
4. If it's a breaking schema change, increment `VERSION` and implement `_migrate_data()`.

---

## Adding a new dialog

1. Create the layout in `src/flow3r/app/ui/MyDialog.ui` using Qt Designer.
2. Recompile with `compile_ui.bat` to generate `src/flow3r/app/layout/my_dialog.py`.
3. Write the widget class in `src/flow3r/app/widgets/my_dialog.py`, inheriting from both the generated layout class and the appropriate Qt base class:

```python
from flow3r.app.layout.my_dialog import Ui_MyDialog
from PySide6.QtWidgets import QDialog

class MyDialog(Ui_MyDialog, QDialog):
    ...
```

---

## Coding style

- **Python 3.11+** — use `list[T]`, `dict[K, V]`, `X | Y` unions. Follow the style of the file you are editing.
- Type hints on all public methods and class attributes.
- `from __future__ import annotations` is present in some files — maintain it where it exists.
- Log with `get_logger(__name__)` from `flow3r.logger`. Remove any `print()` calls before committing.
- Config serialisation errors raise `ConfigError` (from `flow3r.core.config.abc.config`).
- Widgets must not import from `flow3r.app.controller` internals; communicate only via `Controller`'s public signals/slots.

---

## Key conventions

| Topic | Rule |
|---|---|
| Config mutation | Always go through `Controller.transaction()` — never mutate `AppConfig` directly |
| Widget state | `blockSignals(True/False)` around programmatic `setChecked` / `setCurrentIndex` / etc. |
| `QMessageBox` | Write config state *before* calling `exec()` to avoid re-entrant signal issues |
| Implicit groups | Managed automatically by `Controller._update_implicit_groups()` — don't touch manually |
| IDs | Generated as `uuid.uuid4()` strings at dataclass construction time |

---

## Building the docs locally

```bash
uv run mkdocs serve
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).
