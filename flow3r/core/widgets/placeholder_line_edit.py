from __future__ import annotations

from typing import Literal, Optional

from PySide6.QtCore import Signal, Qt, QRegularExpression, QObject, QStringListModel
from flow3r.core.placeholder.placeholder_info import PlaceholderInfo
from flow3r.core.widgets.placeholder_label import PlaceholderLabel
from PySide6.QtGui import QFontMetrics, QSyntaxHighlighter, QTextCharFormat, QTextOption, QIcon, QColor, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCompleter, QPlainTextEdit, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QToolButton, QFrame, QFileDialog, QSizePolicy,
)


class PlaceholderHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, placeholder_names=None):
        super().__init__(doc)
        self.placeholder_names: set[str] = set(placeholder_names) if placeholder_names is not None else set()
        self.regex = QRegularExpression(r"\{([A-Za-z_][A-Za-z0-9_\s]*)\}")

        self.ok_fmt = QTextCharFormat()
        self.bad_fmt = QTextCharFormat()
        self._update_formats()

    def _update_formats(self):
        palette = QApplication.palette()
        self.ok_fmt.setForeground(palette.link().color())          # blue — resolves to a known value
        self.bad_fmt.setForeground(QColor(210, 60, 60))            # muted red — unrecognised placeholder
        self.bad_fmt.setFontUnderline(True)
        self.bad_fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)

    def set_placeholder_names(self, names: list[str]):
        self.placeholder_names = set(names)
        self.rehighlight()

    def set_placeholder_infos(self, infos: list[PlaceholderInfo]):
        """Convenience: accept PlaceholderInfo objects and extract their names."""
        self.set_placeholder_names([p.name for p in infos])

    def highlightBlock(self, text):
        it = self.regex.globalMatch(text)
        while it.hasNext():
            m = it.next()
            name = m.captured(1)
            fmt = self.ok_fmt if name in self.placeholder_names else self.bad_fmt
            self.setFormat(m.capturedStart(0), m.capturedLength(0), fmt)


class PlaceholderLineEdit(QPlainTextEdit):
    """A single-line text editor with syntax highlighting support for {placeholder} syntax."""

    editingFinished = Signal()

    def __init__(self, parent=None, placeholder_names: Optional[list[str]] = None):
        super().__init__(parent)

        # Make it single-line-ish
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTabChangesFocus(True)
        self.document().setDocumentMargin(1)
        self.setMaximumBlockCount(1)  # keep exactly one paragraph

        # Attach syntax highlighter
        self._highlighter = PlaceholderHighlighter(self.document(), placeholder_names)

        # Track last-committed text for editingFinished guard
        self._last_committed: str = ""

        # Look like a QLineEdit (frame, padding, focus outline)
        self.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid palette(mid);
                border-radius: 2px;
                background: palette(Base);
                selection-background-color: palette(Highlight);
                selection-color: palette(HighlightedText);
            }
            QPlainTextEdit:focus {
                border: 1px solid palette(Highlight);
            }
        """)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Lock the vertical scrollbar range to [0, 0].  Qt's drag-select
        # auto-scroll timer calls QScrollBar::setValue() directly, bypassing
        # scrollContentsBy; clamping the range to zero stops it at the source.
        vsb = self.verticalScrollBar()
        vsb.setRange(0, 0)
        vsb.rangeChanged.connect(self._on_vsb_range_changed)

        self._completer: Optional[QCompleter] = None

    def _on_vsb_range_changed(self, minimum: int, maximum: int) -> None:
        if minimum == 0 and maximum == 0:
            return
        self.verticalScrollBar().setRange(0, 0)

    def set_placeholder_names(self, names: list[str]):
        self._highlighter.set_placeholder_names(names)

    def set_placeholder_infos(self, infos: list[PlaceholderInfo]):
        """Convenience: accept PlaceholderInfo objects and extract their names."""
        self._highlighter.set_placeholder_infos(infos)

    # --- QLineEdit-like API ---

    def text(self) -> str:
        return self.toPlainText()

    def setText(self, text: str):
        self.setPlainText(text)
        self._last_committed = text

    # --- editingFinished signal ---

    def _maybe_emit_editing_finished(self):
        current = self.text()
        if current != self._last_committed:
            self._last_committed = current
            self.editingFinished.emit()

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self._maybe_emit_editing_finished()

    def keyPressEvent(self, e):
        # When the completer popup is visible, let it handle navigation / selection
        # keys.  QCompleter installs an event filter on the widget for exactly this;
        # calling e.ignore() lets those events pass through to the filter.
        if self._completer is not None and self._completer.popup().isVisible():
            if e.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape,
                           Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                e.ignore()
                return
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._maybe_emit_editing_finished()
            return
        super().keyPressEvent(e)
        self._show_completer()

    # --- Completer support ---

    def set_completer(self, completer: Optional[QCompleter]) -> None:
        """Attach (or detach) a QCompleter for value history suggestions."""
        if self._completer is not None:
            try:
                self._completer.activated.disconnect(self._insert_completion)
            except RuntimeError:
                pass
        self._completer = completer
        if completer is not None:
            completer.setWidget(self)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.activated.connect(self._insert_completion)

    def _insert_completion(self, text: str) -> None:
        self.setPlainText(text)
        self.moveCursor(QTextCursor.MoveOperation.End)

    def _show_completer(self) -> None:
        """Update the completion prefix and show / hide the popup."""
        if self._completer is None:
            return
        prefix = self.toPlainText()
        self._completer.setCompletionPrefix(prefix)
        if self._completer.completionCount() > 0:
            popup = self._completer.popup()
            popup.setCurrentIndex(self._completer.completionModel().index(0, 0))
            cr = self.cursorRect()
            cr.setLeft(0)
            cr.setWidth(max(
                self.viewport().width(),
                popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width(),
            ))
            self._completer.complete(cr)
        else:
            self._completer.popup().hide()

    # --- Overrides ---

    def focusInEvent(self, e):
        super().focusInEvent(e)
        if self._completer is not None:
            self._show_completer()

    # --- Paste / drop: strip newlines ---

    def insertFromMimeData(self, source):
        text = source.text().replace("\n", " ").replace("\r", "")
        self.insertPlainText(text)

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        # Snap the viewport to the cursor after a drag-select so the text
        # cannot remain hidden horizontally when the mouse is released.
        self.ensureCursorVisible()

    def dropEvent(self, e):
        mime = e.mimeData()
        if mime.hasText():
            from PySide6.QtCore import QMimeData
            clean = QMimeData()
            clean.setText(mime.text().replace("\n", " ").replace("\r", ""))
            e.accept()
            self.insertFromMimeData(clean)
        else:
            super().dropEvent(e)

    # --- Fix vertical "autoscroll on drag" ---

    def scrollContentsBy(self, dx, dy):
        # Vertical scroll is fully blocked by the range lock on the scrollbar.
        # This override is a belt-and-suspenders guard for any remaining dy.
        super().scrollContentsBy(dx, 0)

    # --- Proper height sizing ---

    def sizeHint(self):
        sh = super().sizeHint()
        fm = QFontMetrics(self.font())
        doc_margin = int(self.document().documentMargin())
        # frameWidth() returns 0 when a stylesheet owns the border, so add 1px explicitly
        border = max(self.frameWidth(), 1)
        h = fm.height() + 2 * doc_margin + 2 * border
        sh.setHeight(h)
        return sh

    def minimumSizeHint(self):
        msh = super().minimumSizeHint()
        msh.setHeight(self.sizeHint().height())
        return msh


class PlaceholderTextWidget(QFrame):
    """A QLineEdit-like widget with placeholder syntax highlighting, optional file picker, and preview label."""

    textChanged = Signal()
    editingFinished = Signal()

    def __init__(
        self,
        parent=None,
        text: str = "",
        mode: Literal["text", "file", "folder"] = "text",
        allow_editor: bool = False,
        show_preview: bool = True,
        service=None,
    ):
        super().__init__(parent)

        self.mode = mode
        self.show_preview = show_preview

        # --- Widgets ---
        self.txt_value = PlaceholderLineEdit()
        btn_size = self.txt_value.sizeHint().height()

        self.btn_select_file = QToolButton()
        self.btn_select_file.setIcon(
            QIcon.fromTheme("folder") if mode == "folder" else QIcon.fromTheme("document-open")
        )
        self.btn_select_file.setToolTip("Select folder…" if mode == "folder" else "Select file…")
        self.btn_select_file.setText("…")
        self.btn_select_file.setFixedSize(btn_size, btn_size)

        self.btn_editor = QToolButton()
        self.btn_editor.setToolTip("Open editor…")
        self.btn_editor.setIcon(QIcon.fromTheme("accessories-text-editor", QIcon()))
        self.btn_editor.setText("✎")
        self.btn_editor.setFixedSize(btn_size, btn_size)

        self.lbl_preview = PlaceholderLabel(prefix="Preview: ")

        # --- Layout ---
        self.input_row = QWidget()

        input_row_layout = QHBoxLayout(self.input_row)
        input_row_layout.setContentsMargins(0, 0, 0, 0)
        input_row_layout.setSpacing(2)
        input_row_layout.addWidget(self.txt_value)
        input_row_layout.addWidget(self.btn_select_file)
        input_row_layout.addWidget(self.btn_editor)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(2)
        root.addWidget(self.input_row)
        root.addWidget(self.lbl_preview)

        # --- Connections ---
        self.txt_value.editingFinished.connect(self.editingFinished)
        self.btn_select_file.clicked.connect(self.select_file)
        self.btn_editor.clicked.connect(self.open_editor)

        # Forward text changes: re-render the preview template and emit our own signal
        self.txt_value.textChanged.connect(self._sync_preview_template)
        self.txt_value.textChanged.connect(self.textChanged)

        # --- Initial state ---
        self._placeholder_service = None  # kept so we can disconnect on re-assignment
        self.txt_value.setText(text)
        self.lbl_preview.set_template(text)  # sync initial template
        self.set_mode(mode)
        self.set_allow_editor(allow_editor)
        self.set_show_preview(show_preview)
        if service is not None:
            self.set_placeholder_service(service)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    # --- Public API ---

    def text(self) -> str:
        return self.txt_value.text()

    def setText(self, text: str):
        self.txt_value.setText(text)

    def insertPlainText(self, text: str):
        self.txt_value.insertPlainText(text)

    def set_placeholder_service(self, service) -> None:
        """Attach an IPlaceholderService.

        The preview label subscribes to ``service.changed`` and re-renders
        automatically.  The syntax highlighter is also updated immediately and
        kept in sync via the same signal.
        """
        if self._placeholder_service is not None:
            self._placeholder_service.changed.disconnect(self._sync_highlighter_names)
        self._placeholder_service = service
        self.lbl_preview.set_service(service)
        if service is not None:
            self.txt_value.set_placeholder_infos(service.placeholders)
            service.changed.connect(self._sync_highlighter_names)

    def _sync_preview_template(self) -> None:
        self.lbl_preview.set_template(self.txt_value.text())

    def _sync_highlighter_names(self) -> None:
        if self._placeholder_service is not None:
            # Block signals on txt_value while rehighlighting: QSyntaxHighlighter
            # modifies the document's formatting, which Qt counts as a content
            # change and re-emits QPlainTextEdit.textChanged.  Without the guard
            # this causes an infinite loop:
            #   textChanged → placeholder_named_value_changed → service.changed
            #   → _sync_highlighter_names → rehighlight → textChanged → …
            self.txt_value.blockSignals(True)
            try:
                self.txt_value.set_placeholder_infos(self._placeholder_service.placeholders)
            finally:
                self.txt_value.blockSignals(False)

    def set_mode(self, mode: Literal["text", "file", "folder"]):
        self.mode = mode
        self.btn_select_file.setVisible(mode in ("file", "folder"))
        self.btn_select_file.setIcon(
            QIcon.fromTheme("folder") if mode == "folder" else QIcon.fromTheme("document-open")
        )
        self.btn_select_file.setToolTip(
            "Select folder…" if mode == "folder" else "Select file…"
        )

    def set_allow_editor(self, allow: bool):
        self.btn_editor.setVisible(allow)

    def set_show_preview(self, show: bool):
        self.show_preview = show
        if not show:
            # Disconnect the auto-hide wiring so the label stays hidden
            # regardless of content changes.
            self.lbl_preview.content_changed.disconnect(self.lbl_preview.setVisible)
            self.lbl_preview.setVisible(False)
        else:
            self.lbl_preview.content_changed.connect(self.lbl_preview.setVisible)

    def select_file(self):
        if self.mode == "folder":
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Select File", filter="All Files (*)",
                options=QFileDialog.Option.DontConfirmOverwrite,
            )
        if path:
            self.setText(path)
            self.editingFinished.emit()

    def open_editor(self):
        pass  # TODO

    def set_completion_history(self, values: list[str]) -> None:
        """Attach a QCompleter driven by *values* (most-recent-first) to the input."""
        if not values:
            self.txt_value.set_completer(None)
            return
        model = QStringListModel(values, self.txt_value)
        completer = QCompleter(model, self.txt_value)
        self.txt_value.set_completer(completer)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit
    from flow3r.core.placeholder.placeholder_info import PlaceholderInfo

    PLACEHOLDER_INFOS = [
        PlaceholderInfo("frame",      "Frame Number"),
        PlaceholderInfo("timestamp",  "Timestamp"),
        PlaceholderInfo("camera_id",  "Camera ID"),
        PlaceholderInfo("session",    "Session"),
        PlaceholderInfo("index",      "Index"),
        # Simulated system placeholders
        PlaceholderInfo("group_name",           "Group Name"),
        PlaceholderInfo("recording_number",     "Recording Number"),
        PlaceholderInfo("recording_start_time", "Recording Start Time"),
    ]
    PLACEHOLDER_NAMES = [p.name for p in PLACEHOLDER_INFOS]

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("PlaceholderLineEdit / PlaceholderTextWidget Test")
    window.resize(600, 400)

    root_layout = QVBoxLayout(window)

    hint_label = QLabel(f"Known placeholders: {', '.join('{' + p.name + '} (' + p.label + ')' for p in PLACEHOLDER_INFOS)}")
    hint_label.setStyleSheet("color: grey; font-size: 10px;")
    root_layout.addWidget(hint_label)

    # --- QLineEdit reference rows ---
    root_layout.addWidget(QLabel("<b>QLineEdit (reference)</b>"))
    ref_form = QFormLayout()
    ref_form.setContentsMargins(0, 0, 0, 0)
    root_layout.addLayout(ref_form)

    ref_le = QLineEdit("{frame}_{timestamp}_{camera_id}")
    ref_form.addRow("plain", ref_le)

    ref_row_widget = QWidget()
    ref_row = QHBoxLayout(ref_row_widget)
    ref_row.setContentsMargins(0, 0, 0, 0)
    ref_row.setSpacing(2)
    ref_le2 = QLineEdit("{frame}_{timestamp}_{camera_id}")
    ref_btn1 = QToolButton(); ref_btn1.setText("…")
    ref_btn2 = QToolButton(); ref_btn2.setText("✎")
    ref_row.addWidget(ref_le2)
    ref_row.addWidget(ref_btn1)
    ref_row.addWidget(ref_btn2)
    ref_form.addRow("with buttons", ref_row_widget)

    # --- PlaceholderLineEdit section ---
    root_layout.addWidget(QLabel("<b>PlaceholderLineEdit</b>"))
    le_form = QFormLayout()
    le_form.setContentsMargins(0, 0, 0, 0)
    root_layout.addLayout(le_form)

    status_label = QLabel("editingFinished: (not yet emitted)")
    status_label.setStyleSheet("color: grey; font-size: 10px;")

    le_examples = [
        ("All valid",       "{frame}_{timestamp}_{camera_id}"),
        ("Mixed valid/bad", "{frame}_{unknown_key}_{session}"),
        ("No placeholders", "plain text, no placeholders"),
        ("Empty",           ""),
    ]
    for label, initial_text in le_examples:
        w = PlaceholderLineEdit(placeholder_names=PLACEHOLDER_NAMES)
        w.setText(initial_text)
        w.editingFinished.connect(
            lambda _w=w: status_label.setText(f'editingFinished: "{_w.text()}"')
        )
        le_form.addRow(label, w)

    root_layout.addWidget(status_label)

    # --- PlaceholderTextWidget section ---
    root_layout.addWidget(QLabel("<b>PlaceholderTextWidget</b>"))
    ptw_form = QFormLayout()
    ptw_form.setContentsMargins(0, 0, 0, 0)
    root_layout.addLayout(ptw_form)

    provider = {
        "frame": 42,
        "timestamp": "2026-05-05T12:00:00",
        "camera_id": "cam0",
        "session": "session_01",
        "index": 7,
        "group_name": "Group A",
        "recording_number": 1,
        "recording_start_time": "2026-05-05T12:00:00",
    }

    # Minimal mock service so we can exercise set_placeholder_service / service= kwarg
    class _MockService(QObject):
        changed = Signal()

        def __init__(self, infos, values):
            super().__init__()
            self._infos = infos
            self._values = values

        @property
        def placeholders(self):
            return self._infos

        @property
        def values(self):
            return self._values

    mock_service = _MockService(PLACEHOLDER_INFOS, provider)

    ptw_examples = [
        ("text (service=)",    "text",   "{session}/{camera_id}_{frame}"),
        ("file (service=)",    "file",   "{session}/{camera_id}_{frame}.mp4"),
        ("folder (no svc)",    "folder", "{session}/{camera_id}"),
        ("sys placeholders",   "text",   "{group_name}/rec_{recording_number}"),
    ]
    for label, mode, initial_text in ptw_examples:
        w = PlaceholderTextWidget(
            mode=mode, text=initial_text,
            service=mock_service if mode != "folder" else None,
        )
        ptw_form.addRow(label, w.txt_value)
        ptw_form.addRow(None, w.lbl_preview)

    root_layout.addStretch()
    window.show()
    sys.exit(app.exec())
