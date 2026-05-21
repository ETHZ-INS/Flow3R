# UI Widgets — Agent Instructions

- Widgets are **read-only consumers** of config snapshots. Do not write to `AppConfig` directly.
- All config changes go through `Controller`'s public signals/slots only.
- Do **not** import from `flow3r.app.controller` implementation internals.
- Request an initial config snapshot in `__init__` via the `config_snapshot_requested` signal.
- Use `blockSignals(True) / blockSignals(False)` around all programmatic widget state changes (`setChecked`, `setCurrentIndex`, `setKeySequence`, etc.).
- Decorate every slot method with `@Slot(...)`.
- Write config state **before** calling `QMessageBox.exec()` — modal dialogs spin the event loop.

See `docs/agent/ui-layer.md` for full details.

