# UI Source Files — Agent Instructions

- Files here are Qt Designer XML (`.ui`). Do not treat them as plain text.
- Do **not** use standard find/replace or insert tools — whitespace differences cause silent failures.

## Editing a `.ui` file

Always use PowerShell:

```powershell
$content = [System.IO.File]::ReadAllText("path\to\File.ui")
$content = $content -replace 'old string', 'new string'
[System.IO.File]::WriteAllText("path\to\File.ui", $content)
```

## After every edit — recompile

```powershell
conda run -n GrimaceRecorder pyside6-uic "src/flow3r/app/ui/MyDialog.ui" -o "src/flow3r/app/layout/my_dialog.py"
```

- Do **not** edit anything in `src/flow3r/app/layout/` — overwritten by the compiler.

