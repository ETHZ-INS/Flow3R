# UI Layer Guide

## Overview

- Each dialog/widget is a hand-written class in `src/flow3r/app/widgets/`.
- Layouts are defined as Qt Designer XML in `src/flow3r/app/ui/`.
- Compiled Python layouts live in `src/flow3r/app/layout/` — **never edit these by hand**.
- Widget classes use multiple inheritance: `class MyDialog(Ui_MyDialog, QDialog)`.

## Widgets are read-only consumers

- Widgets **must not** write to `AppConfig` directly.
- All changes go through `Controller`'s public signals/slots only.
- Do **not** import from `flow3r.app.controller` implementation internals in widget code.
- Request an initial config snapshot in `__init__` via the `config_snapshot_requested` signal.

## Editing `.ui` files programmatically

Standard text-replacement tools **do not reliably write to `.ui` files** — whitespace differences cause silent failures. Always use PowerShell:

```powershell
$content = [System.IO.File]::ReadAllText("path\to\File.ui")
$content = $content -replace 'old string', 'new string'
[System.IO.File]::WriteAllText("path\to\File.ui", $content)
```

Then recompile:

```powershell
conda run -n GrimaceRecorder pyside6-uic "src/flow3r/app/ui/MyDialog.ui" -o "src/flow3r/app/layout/my_dialog.py"
```

## Adding a new dialog — checklist

1. Create `src/flow3r/app/ui/MyDialog.ui` in Qt Designer.
2. Recompile to generate `src/flow3r/app/layout/my_dialog.py`.
3. Write `src/flow3r/app/widgets/my_dialog.py` inheriting from `Ui_MyDialog` and the Qt base class.
4. Never edit the generated layout file.

## Signals and slots

- Decorate every slot with `@Slot(...)`.
- Use `blockSignals(True) / blockSignals(False)` around programmatic `setChecked`, `setCurrentIndex`, `setKeySequence`, etc. to prevent re-entrant handlers.
- Connect a signal/slot pair only once; call `disconnect()` before reconnecting if needed.
- Write config state **before** calling `QMessageBox.exec()` — modal dialogs spin the Qt event loop.

