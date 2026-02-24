from datetime import datetime
from typing import Optional

from PySide6.QtCore import Signal, Slot, QTimer
from PySide6.QtWidgets import QMenu, QWidget

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.layout.recording_controls_widget import Ui_RecordingControlsWidget
from flow3r.app.session_state import SessionStateBase, Ready, Running, AcquisitionFinished, FinishingProcessing, \
    FinishingRecording, NotReady, MissingInfo, Error, ConfigError, InvalidPlaceholders


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
        self.state: SessionStateBase = NotReady()

        self.start_time: Optional[datetime] = None
        self.timer = QTimer(self)

        self.context_menu = QMenu(self)
        self.action_configure_group = self.context_menu.addAction("Configure Group")
        self.action_configure_group.triggered.connect(self._configure_group)

        self.lbl_group_name.setText(group_name)

        self.lbl_status.linkActivated.connect(self._status_link_clicked)
        self.btn_start.clicked.connect(self._start_recording)
        self.timer.timeout.connect(self._update_timer)

    def request_active_session(self):
        self.active_session_requested.emit(self.group_id)

    def group_changed(self, group_config: GroupConfig):
        if self.group_id != group_config.id:
            return
        self.group_name = group_config.name
        self._update_group_name_label()

    def _update_group_name_label(self):
        self.lbl_group_name.setText(self.group_name)

    def set_active_session(self, group_id: str, session_id: str, state: SessionStateBase):
        if group_id != self.group_id:
            return

        print(f"Active session changed for group {group_id}: {session_id}")

        self.session_id = session_id
        self.set_session_state(group_id, session_id, state)

    def set_session_state(self, group_id: str, session_id: str, state: SessionStateBase):
        if group_id != self.group_id or session_id != self.session_id:
            return

        print(f"Session state changed for {group_id}/{session_id}: {state}")

        self.state = state
        self._update_lbl_status()

        if isinstance(state, Ready):
            self.btn_start.setText("Start")
        elif isinstance(state, Running):
            self.btn_start.setText("Stop")

        if isinstance(state, Running):
            self._ensure_timer_running(state.start_time)
        elif isinstance(state, AcquisitionFinished):
            self._stop_timer(state.end_time)
        else:
            self._stop_timer()

    def _update_btn_start(self):
        enabled = self.session_id is not None and isinstance(self.state, (Ready, Running))
        self.btn_start.setEnabled(enabled)

        if isinstance(self.state, Running):
            self.btn_start.setText("Stop")
        else:
            self.btn_start.setText("Start")
            
    def _update_lbl_status(self):
        if isinstance(self.state, Ready):
            self.lbl_status.setText("Ready - <a href=\"fill_placeholders\">Edit Information</a>")
            self.lbl_status.setStyleSheet("QLabel { color: black; }")
        elif isinstance(self.state, Running):
            if isinstance(self.state, FinishingProcessing):
                self.lbl_status.setText(f"Finishing processing ({self.state.processing_progress*100:.0f}%)...")
                self.lbl_status.setStyleSheet("QLabel { color: orange; }")
            elif isinstance(self.state, FinishingRecording):
                self.lbl_status.setText("Finishing recording...")
                self.lbl_status.setStyleSheet("QLabel { color: green; }")
            else:
                self.lbl_status.setText("Recording...")
                self.lbl_status.setStyleSheet("QLabel { color: green; }")
        elif isinstance(self.state, NotReady):
            if isinstance(self.state, MissingInfo):
                self.lbl_status.setText("Not Ready: <a href=\"fill_placeholders\">Missing Information</a>")
            else:
                self.lbl_status.setText(f"Not Ready: {self.state.reason}")
            self.lbl_status.setStyleSheet("QLabel { color: red; }")
        elif isinstance(self.state, Error):
            if isinstance(self.state, ConfigError):
                self.lbl_status.setText(f"Config Error: <a href=\"config_error\">{self.state.message}</a>")
            elif isinstance(self.state, InvalidPlaceholders):
                self.lbl_status.setText(f"Error: invalid placeholders: {', '.join(self.state.invalid_placeholders)}")
            else:
                self.lbl_status.setText(f"Error: {self.state.message}")
            self.lbl_status.setStyleSheet("QLabel { color: red; }")
        else:
            self.lbl_status.setText("")
            self.lbl_status.setStyleSheet("QLabel { color: black; }")

    def _ensure_timer_running(self, start_time: datetime):
        if not self.timer.isActive():
            self.start_time = start_time
            self.timer.start(1000)  # Update every second
        else:
            self.start_time = start_time

    def _stop_timer(self, stop_time: Optional[datetime] = None):
        self.timer.stop()
        if stop_time is None or self.start_time is None:
            self.lbl_recording_time.setText("00:00:00")
            return

        elapsed = stop_time - self.start_time
        time_str = str(elapsed).split(".")[0]  # Format as HH:MM:SS
        self.lbl_recording_time.setText(time_str)

    def _update_timer(self):
        assert self.start_time is not None
        elapsed = datetime.now() - self.start_time
        time_str = str(elapsed).split(".")[0]  # Format as HH:MM:SS
        self.lbl_recording_time.setText(time_str)

    def _configure_group(self):
        self.edit_group.emit(self.group_id)

    def _start_recording(self):
        if not self.session_id:
            return
        print(f"Recording {self.session_id} {self.state}")
        if isinstance(self.state, Running):
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
