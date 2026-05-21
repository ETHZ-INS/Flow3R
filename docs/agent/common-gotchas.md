# Common Gotchas & Coding Style

## Gotchas

| Problem | Solution |
|---|---|
| `.ui` file edit not persisted | Use PowerShell `WriteAllText` — standard text-replacement tools silently fail on `.ui` files |
| `pyside6-uic` produces stale output | Ensure the `.ui` file is written to disk before running the compiler |
| `QKeySequence` shortcut ambiguity | Register one `QShortcut` per unique key string; iterate all groups mapped to it on activation |
| `QMessageBox` causes re-entrant signal | Write config state *before* calling `QMessageBox.warning/exec()` |
| `blockSignals` missing | Use around programmatic `setChecked/setCurrentIndex/setKeySequence` calls |
| New config field breaks old project files | Always `data.get("field", default)` — never `data["field"]` for new fields |
| `setRowVisible` on `QFormLayout` | Call on the **layout** object: `frm.layout().setRowVisible(widget, bool)` |
| Implicit group modified manually | Don't — managed by `Controller._update_implicit_groups()` |

## Coding style

- **Python 3.11+** — use `list[T]`, `dict[K, V]`, `X | Y`. Follow the style of the file being edited.
- Type hints on all public methods and class attributes.
- Maintain `from __future__ import annotations` where already present.
- No abbreviations except established domain terms (`ph` for placeholder in local scope is fine).
- Prefer `deepcopy` when passing config objects out of the controller or between dialogs.
- Remove all `print()` calls before committing — use `get_logger(__name__)` instead.

