from typing import Optional

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QMenu, QWidget

from aaaflow3r.app.config.group_config import GroupConfig
from aaaflow3r.app.layout.recording_controls_widget import Ui_RecordingControlsWidget


class RecordingControlsWidget(Ui_RecordingControlsWidget, QWidget):
    recording_start = Signal(str, str)  # group_id, session_id
    recording_stop = Signal(str, str)  # group_id, session_id
    recording_detach = Signal(str, int)  # group_id, session_id

    active_session_requested = Signal(str)

    goto = Signal(list)  # Signal to open a config dialog
    edit_group = Signal(str)  # group_id

    def __init__(self, group_id: str, group_name: str, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.group_id = group_id
        self.group_name: Optional[str] = None
        self.session_id: Optional[str] = None
        self.state = "idle"

        self.context_menu = QMenu(self)
        self.action_configure_group = self.context_menu.addAction("Configure Group")
        self.action_configure_group.triggered.connect(self._configure_group)

        self.lbl_group_name.setText(group_name)

        self.lbl_status.linkActivated.connect(self._status_link_clicked)
        self.btn_start.clicked.connect(self._start_recording)

    def request_active_session(self):
        self.active_session_requested.emit(self.group_id)

    def group_changed(self, group_config: GroupConfig):
        if self.group_id != group_config.id:
            return
        self.group_name = group_config.name
        self._update_group_name_label()

    def _update_group_name_label(self):
        self.lbl_group_name.setText(self.group_name)

    def set_active_session(self, group_id: str, session_id: str):
        if group_id != self.group_id:
            return
        self.session_id = session_id
        self.set_session_state(group_id, session_id, "idle")

    def set_session_state(self, group_id: str, session_id: str, state: str):
        print(f"Session state changed: {group_id} {session_id} {state}")
        if group_id != self.group_id or session_id != self.session_id:
            return
        print(f"Set session state: {state}")
        self.state = state
        if state == "idle":
            self.btn_start.setText("Start")
            self.lbl_status.setText("Ready")
        elif state == "recording":
            self.btn_start.setText("Stop")
            self.lbl_status.setText("Recording...")

    def _configure_group(self):
        self.edit_group.emit(self.group_id)

    def _start_recording(self):
        if not self.session_id:
            return
        print(f"Recording {self.session_id} {self.state}")
        if self.state == "recording":
            self.recording_stop.emit(self.group_id, self.session_id)
        else:
            self.recording_start.emit(self.group_id, self.session_id)

    def _status_link_clicked(self, link: str):
        self.goto.emit([link])

    @Slot(object)
    def _group_config_changed(self, group_config):
        self.lbl_group_name.setText(group_config.name)

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())
