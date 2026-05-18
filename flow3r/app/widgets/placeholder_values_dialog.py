import json
from typing import Any, Dict, List, Optional, Literal

from PySide6.QtCore import Qt, QMargins, QSize, QSettings, Signal, Slot, QObject
from PySide6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QDialogButtonBox, QWidget, QFormLayout,
    QTabWidget, QPushButton, QScrollArea,
)

from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.placeholder_config import PlaceholderConfig
from flow3r.app.controller.controller import Controller
from flow3r.core.widgets.placeholder_line_edit import PlaceholderTextWidget
from flow3r.core.api.app.app_context import IAppContext


class LocalPlaceholderService(QObject):
    """Ephemeral IPlaceholderService used inside PlaceholderValuesDialog.

    Cloned from the real service on construction; updated live as the user
    edits placeholder values in the dialog.  Never writes back to the real
    service — the dialog commits via the controller on close.
    """

    changed = Signal()
    group_values_changed = Signal(str, object)  # satisfies protocol; unused here

    def __init__(self, real_service, parent=None):
        super().__init__(parent)
        self._placeholders = list(real_service.placeholders)
        self._values: Dict[str, Any] = dict(real_service.values)

    @property
    def placeholders(self):
        return self._placeholders

    @property
    def names(self):
        return [p.name for p in self._placeholders]

    @property
    def values(self) -> Dict[str, Any]:
        return self._values

    @Slot(str, str)
    def update_value(self, name: str, value: str) -> None:
        self._values[name] = value
        self.changed.emit()


class PlaceholderFormSection(QWidget):
    """Input form for a list of PlaceholderConfig objects.

    Tracks current values internally and exposes ``get_values()`` /
    ``has_missing()``.  Emits ``value_changed`` on every edit and
    ``placeholder_named_value_changed(name, value)`` for live preview updates.
    """

    value_changed = Signal()
    placeholder_named_value_changed = Signal(str, str)  # (placeholder_name, value)

    def __init__(
        self,
        placeholders: List[PlaceholderConfig],
        values: Dict[str, str],
        show_constants: bool = True,
        service=None,
        parent=None,
    ):
        super().__init__(parent)
        self._widgets: Dict[str, PlaceholderTextWidget] = {}

        _layout = QFormLayout(self)
        _layout.setContentsMargins(QMargins(0, 0, 0, 0))

        constant_phs = [p for p in placeholders if p.is_constant]
        input_phs    = [p for p in placeholders if not p.is_constant]

        if show_constants and constant_phs:
            _layout.addRow(QLabel("### Constants", textFormat=Qt.TextFormat.MarkdownText))
            for ph in constant_phs:
                _layout.addRow(f"{ph.label}:", QLabel(str(ph.constant_value)))
            _layout.addRow("", QWidget())  # spacer

        if input_phs:
            if show_constants:
                _layout.addRow(QLabel("### Placeholders", textFormat=Qt.TextFormat.MarkdownText))
            for ph in input_phs:
                mode: Literal["text", "file", "folder"] = ph.type if ph.type in ("file", "folder") else "text"
                ptw = PlaceholderTextWidget(
                    mode=mode,
                    text=values.get(ph.id, ""),
                    allow_editor=False,
                    service=service,
                    parent=self,
                )
                ptw.textChanged.connect(self.value_changed)
                # Emit (name, value) so the dialog can push edits to the local
                # service live.  Lambda is safe: ptw and this section share
                # the same parent lifetime so no dangling connection is possible.
                ptw.textChanged.connect(
                    lambda _name=ph.name, _ptw=ptw: self.placeholder_named_value_changed.emit(_name, _ptw.text())
                )
                _layout.addRow(f"{ph.label}:", ptw.input_row)
                _layout.addRow(QLabel(""), ptw.lbl_preview)
                _layout.labelForField(ptw.lbl_preview).setVisible(False)

                self._widgets[ph.id] = ptw

    def get_values(self) -> Dict[str, str]:
        return {pid: ptw.text() for pid, ptw in self._widgets.items()}

    def has_missing(self) -> bool:
        return any(not ptw.text() for ptw in self._widgets.values())

    def set_completion_histories(self, histories: Dict[str, List[str]]) -> None:
        """Apply per-placeholder completion history to each input widget."""
        for ph_id, ptw in self._widgets.items():
            hist = histories.get(ph_id, [])
            if hist:
                ptw.set_completion_history(hist)


class PlaceholderValuesDialog(QDialog):
    """Dialog for editing global and/or group placeholder values.

    Modes
    -----
    ``"browse"``
        Shows all groups in a tab widget.  Single "Close" button — always saves.
    ``"record"``
        ``group_id`` must be supplied.  Shows global + that one group in a flat
        scrollable form.  When *show_start_button* is True, shows a "Start
        Recording" button (locked until all fields filled) alongside "Close"
        (saves without starting).  When False, shows only "Close".
    """

    values_updated = Signal(object, object)  # (global_dict, group_dict)
    auto_start_requested = Signal(str, str)  # group_id, session_id — emitted only when "Start Recording" is clicked

    def __init__(
        self,
        app_context: IAppContext,
        controller: Controller,
        mode: Literal["browse", "record"] = "browse",
        group_id: Optional[str] = None,
        session_id: Optional[str] = None,
        show_start_button: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        assert mode != "record" or group_id is not None, \
            "group_id is required in record mode"

        self.controller = controller
        self._mode = mode
        self._target_group_id = group_id
        self._session_id = session_id

        # Clone the real service into a local one that updates live while the
        # user edits.  The real service is only updated when the dialog closes.
        self._local_service = LocalPlaceholderService(
            app_context.placeholder_service, parent=self
        )

        self._global_section: Optional[PlaceholderFormSection] = None
        self._group_sections: Dict[str, PlaceholderFormSection] = {}
        self._tab_widget: Optional[QTabWidget] = None
        self._start_btn: Optional[QPushButton] = None
        self._group_tab_names: Dict[str, str] = {}  # group_id -> base name

        self.setWindowTitle("Placeholders")
        self.resize(QSize(600, 450))

        self._committed = False
        self._start_requested = False
        self._outer_layout = QVBoxLayout(self)

        self._button_box = QDialogButtonBox(self)
        if mode == "record" and show_start_button:
            start_btn = QPushButton("Start Recording")
            start_btn.setEnabled(False)
            self._start_btn = start_btn
            self._button_box.addButton(start_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        self._button_box.addButton(QPushButton("Close"), QDialogButtonBox.ButtonRole.RejectRole)
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self._on_close)

        self.values_updated.connect(self.controller.update_placeholder_values)
        self.controller.config_snapshot.connect(self._on_config_snapshot)
        self.controller.send_config_snapshot()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_section(self, placeholders, values, show_constants) -> PlaceholderFormSection:
        """Create a PlaceholderFormSection wired to the local service."""
        sec = PlaceholderFormSection(
            placeholders, values,
            show_constants=show_constants,
            service=self._local_service,
        )
        sec.placeholder_named_value_changed.connect(self._local_service.update_value)
        return sec

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _on_config_snapshot(self, config: AppConfig):
        self.controller.config_snapshot.disconnect(self._on_config_snapshot)
        all_phs    = list(config.placeholders.values())
        global_phs = [p for p in all_phs if p.is_global]
        group_phs  = [p for p in all_phs if not p.is_global]
        if self._mode == "record":
            self._build_single_group_ui(config, global_phs, group_phs)
        else:
            self._build_all_groups_ui(config, global_phs, group_phs)
        self._outer_layout.addWidget(self._button_box)
        self._update_start_button()
        self._apply_histories(config)
        self.adjustSize()

    def _build_single_group_ui(self, config, global_phs, group_phs):
        group_id = self._target_group_id
        assert group_id is not None
        group_name = config.all_groups[group_id].name if group_id in config.all_groups else group_id

        scroll    = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vl        = QVBoxLayout(container)
        vl.setAlignment(Qt.AlignmentFlag.AlignTop)

        if global_phs:
            #vl.addWidget(QLabel("### Global Placeholders", textFormat=Qt.TextFormat.MarkdownText))
            sec = self._make_section(global_phs, config.global_placeholder_values, show_constants=True)
            sec.value_changed.connect(self._update_start_button)
            self._global_section = sec
            vl.addWidget(sec)

        if group_phs:
            vl.addWidget(QLabel(f"### {group_name}", textFormat=Qt.TextFormat.MarkdownText))
            group_vals = config.group_placeholder_values.get(group_id, {})
            sec = self._make_section(group_phs, group_vals, show_constants=False)
            sec.value_changed.connect(self._update_start_button)
            self._group_sections[group_id] = sec
            vl.addWidget(sec)

        scroll.setWidget(container)
        self._outer_layout.addWidget(scroll)

    def _build_all_groups_ui(self, config, global_phs, group_phs):
        if not group_phs:
            if global_phs:
                sec = self._make_section(global_phs, config.global_placeholder_values, show_constants=True)
                self._global_section = sec
                self._outer_layout.addWidget(sec)
            else:
                self._outer_layout.addWidget(QLabel("No placeholders defined."))
            return

        tab_widget = QTabWidget()
        self._tab_widget = tab_widget

        global_tab = QWidget()
        gtl = QVBoxLayout(global_tab)
        gtl.setAlignment(Qt.AlignmentFlag.AlignTop)
        if global_phs:
            sec = self._make_section(global_phs, config.global_placeholder_values, show_constants=True)
            sec.value_changed.connect(self._refresh_tab_labels)
            self._global_section = sec
            gtl.addWidget(sec)
        else:
            gtl.addWidget(QLabel("No global placeholders defined."))
        tab_widget.addTab(global_tab, "Global")

        for gid, group_config in config.all_groups.items():
            tab = QWidget()
            tl  = QVBoxLayout(tab)
            tl.setAlignment(Qt.AlignmentFlag.AlignTop)
            group_vals = config.group_placeholder_values.get(gid, {})
            sec = self._make_section(group_phs, group_vals, show_constants=False)
            sec.value_changed.connect(self._refresh_tab_labels)
            self._group_sections[gid] = sec
            tl.addWidget(sec)
            self._group_tab_names[gid] = group_config.name
            tab_widget.addTab(tab, group_config.name)

        self._outer_layout.addWidget(tab_widget)
        self._refresh_tab_labels()

    # ------------------------------------------------------------------
    # Tab label refresh
    # ------------------------------------------------------------------

    def _refresh_tab_labels(self):
        if self._tab_widget is None:
            return
        global_missing = self._global_section is not None and self._global_section.has_missing()
        self._tab_widget.setTabText(0, "⚠ Global" if global_missing else "Global")
        for i, (gid, sec) in enumerate(self._group_sections.items(), start=1):
            base = self._group_tab_names.get(gid, gid)
            self._tab_widget.setTabText(i, f"⚠ {base}" if sec.has_missing() else base)

    # ------------------------------------------------------------------
    # Start button state
    # ------------------------------------------------------------------

    def _update_start_button(self):
        if self._start_btn is None:
            return
        global_ok = self._global_section is None or not self._global_section.has_missing()
        group_ok  = all(not s.has_missing() for s in self._group_sections.values())
        self._start_btn.setEnabled(global_ok and group_ok)

    # ------------------------------------------------------------------
    # Value history (QSettings — machine-scoped, not in project files)
    # ------------------------------------------------------------------

    _HISTORY_ORG = "ETH3RHub"
    _HISTORY_APP = "Flow3R"
    _HISTORY_MAX = 10

    @staticmethod
    def _history_settings() -> QSettings:
        return QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                         PlaceholderValuesDialog._HISTORY_ORG,
                         PlaceholderValuesDialog._HISTORY_APP)

    def _apply_histories(self, config: AppConfig) -> None:
        """Load per-placeholder value histories from QSettings and populate completers."""
        settings = self._history_settings()
        histories: Dict[str, List[str]] = {}
        for ph in config.placeholders.values():
            if ph.is_constant:
                continue
            raw = settings.value(f"placeholder_history/{ph.id}", None)
            if raw:
                try:
                    histories[ph.id] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    pass

        if self._global_section is not None:
            self._global_section.set_completion_histories(histories)
        for sec in self._group_sections.values():
            sec.set_completion_histories(histories)

    def _save_histories(self) -> None:
        """Persist submitted placeholder values into the QSettings history store."""
        settings = self._history_settings()

        all_values: Dict[str, str] = {}
        if self._global_section is not None:
            all_values.update(self._global_section.get_values())
        for sec in self._group_sections.values():
            all_values.update(sec.get_values())

        for ph_id, value in all_values.items():
            if not value:
                continue
            raw = settings.value(f"placeholder_history/{ph_id}", None)
            try:
                hist: List[str] = json.loads(raw) if raw else []
            except (json.JSONDecodeError, TypeError):
                hist = []
            # Deduplicate, prepend newest, cap at HISTORY_MAX
            hist = [v for v in hist if v != value]
            hist.insert(0, value)
            hist = hist[:self._HISTORY_MAX]
            settings.setValue(f"placeholder_history/{ph_id}", json.dumps(hist))

    # ------------------------------------------------------------------
    # Save & close
    # ------------------------------------------------------------------

    def _collect_and_emit(self):
        global_vals = self._global_section.get_values() if self._global_section else {}
        group_vals  = {gid: s.get_values() for gid, s in self._group_sections.items()}
        self.values_updated.emit(global_vals, group_vals)

    def _commit_once(self) -> None:
        """Ensure _collect_and_emit is called exactly once, regardless of close path."""
        if not self._committed:
            self._committed = True
            self._save_histories()
            self._collect_and_emit()

    def _on_accept(self):
        self._start_requested = True
        self.accept()

    def _on_close(self):
        self.reject()

    # Override accept/reject so that all close paths (buttons, Escape, programmatic)
    # go through _commit_once before the dialog hides.
    def accept(self):
        self._commit_once()
        if self._start_requested and self._target_group_id is not None and self._session_id is not None:
            self.auto_start_requested.emit(self._target_group_id, self._session_id)
        super().accept()

    def reject(self):
        self._commit_once()
        super().reject()

    def closeEvent(self, event):
        # Handles the window X button in non-exec() (modeless) usage where
        # reject() is not automatically called by QDialog::closeEvent.
        self._commit_once()
        super().closeEvent(event)
