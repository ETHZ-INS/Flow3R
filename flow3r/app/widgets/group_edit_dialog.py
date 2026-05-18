from typing import Optional, Set

from PySide6.QtCore import QTime
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QDialog, QLayout, QMessageBox

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.layout.group_edit_dialog import Ui_GroupEditDialog


class GroupEditDialog(Ui_GroupEditDialog, QDialog):
    def __init__(self, config: GroupConfig, existing_shortcut_keys: Optional[Set[str]] = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.frm_recording_configuration.setMinimumWidth(400)

        # Limit to a single key chord (Ctrl+A counts as 1; Ctrl+K,Ctrl+A would be 2)
        self.key_shortcut.setMaximumSequenceLength(1)

        # Keys already assigned to other groups — used for duplicate warning
        self._existing_shortcut_keys: Set[str] = existing_shortcut_keys or set()

        self.recording_form_groups = {
            "manual": [],
            "timed": [self.tme_duration]
        }

        self.config = config

        if self.config.implicit:
            self.txt_recording_name.setReadOnly(True)

        self.dpd_recording_mode.clear()
        for recording_mode, recording_mode_name in GroupConfig.RECORDING_MODES.items():
            self.dpd_recording_mode.addItem(recording_mode_name, recording_mode)

        self.dpd_recording_mode.currentIndexChanged.connect(self.recording_mode_changed)
        self.txt_recording_name.editingFinished.connect(self.group_name_changed)
        self.tme_duration.timeChanged.connect(self.recording_duration_changed)
        self.key_shortcut.keySequenceChanged.connect(self.shortcut_key_changed)

        self.update_all()

    def _switch_recording_form_group(self):
        recording_mode = self.config.recording_config.recording_mode

        for group_recording_mode, rows in self.recording_form_groups.items():
            if group_recording_mode == recording_mode:
                continue

            for row in rows:
                if self.frm_recording_configuration.layout().isRowVisible(row):
                    self.frm_recording_configuration.layout().setRowVisible(row, False)

        for row in self.recording_form_groups.get(recording_mode, []):
            if not self.frm_recording_configuration.layout().isRowVisible(row):
                self.frm_recording_configuration.layout().setRowVisible(row, True)

    def update_txt_recording_name(self):
        self.txt_recording_name.setText(self.config.name)

    def update_dpd_recording_mode(self):
        self.dpd_recording_mode.setCurrentIndex(self.dpd_recording_mode.findData(self.config.recording_config.recording_mode))

    def update_tme_duration(self):
        self.tme_duration.setTime(QTime.fromMSecsSinceStartOfDay(int(self.config.recording_config.recording_duration * 1000)))

    def update_key_shortcut(self):
        self.key_shortcut.blockSignals(True)
        try:
            key = self.config.recording_config.shortcut_key or ""
            self.key_shortcut.setKeySequence(QKeySequence(key))
        finally:
            self.key_shortcut.blockSignals(False)

    def update_all(self):
        self._switch_recording_form_group()
        self.update_txt_recording_name()
        self.update_dpd_recording_mode()
        self.update_tme_duration()
        self.update_key_shortcut()

    def group_name_changed(self):
        name = self.txt_recording_name.text()
        self.config.name = name

    def recording_mode_changed(self):
        recording_mode = self.dpd_recording_mode.itemData(self.dpd_recording_mode.currentIndex())
        self.config.recording_config.recording_mode = recording_mode
        self._switch_recording_form_group()

    def recording_duration_changed(self):
        duration: QTime = self.tme_duration.time()
        self.config.recording_config.recording_duration = duration.msecsSinceStartOfDay() / 1000.0  # Convert to seconds

    def shortcut_key_changed(self, key_sequence: QKeySequence):
        text = key_sequence.toString()
        new_value = text if text else None

        # Guard against spurious re-emissions (focus-loss finalisation, setKeySequence, etc.)
        if new_value == self.config.recording_config.shortcut_key:
            return

        # Write before showing the warning: QMessageBox spins the event loop, which can cause
        # the QKeySequenceEdit finalization timer to re-emit keySequenceChanged. Writing first
        # ensures that re-entrant call is caught by the guard above.
        self.config.recording_config.shortcut_key = new_value

        if new_value and new_value in self._existing_shortcut_keys:
            QMessageBox.warning(
                self,
                "Duplicate Shortcut",
                f"The shortcut <b>{new_value}</b> is already assigned to another group.<br>"
                "Both groups will be triggered together.",
            )

