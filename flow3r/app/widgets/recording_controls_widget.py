from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QMenu, QWidget, QMessageBox, QLabel

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.layout.recording_controls_widget import Ui_RecordingControlsWidget
from flow3r.app.controller.session_state import SessionStateBase, Ready, Running, AcquisitionFinished, \
    FinishingProcessing, \
    FinishingRecording, NotReady, MissingInfo, Error, ConfigError, InvalidPlaceholders, Started


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setStyleSheet("color: grey;")

    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("color: grey; text-decoration: underline;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.setStyleSheet("color: grey;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


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

        self.frm_preview.setVisible(False)
        self.lbl_recording_time.setText("0:00:00")

        self.lbl_duration.deleteLater()
        self.lbl_duration = ClickableLabel(text="/ -:--:--", parent=self.frm_controls)
        self.lbl_duration.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        self.frm_controls.layout().addWidget(self.lbl_duration)
        self.lbl_duration.setToolTip(
            "Click to configure recording duration"
        )

        self.group_id = group_id
        self.group_name: Optional[str] = group_name
        self.session_id: Optional[str] = None
        self.state: SessionStateBase = NotReady(recording_number=None)

        self.start_time: Optional[datetime] = None
        self.timer = QTimer(self)

        self.context_menu = QMenu(self)
        self.action_configure_group = self.context_menu.addAction("Configure Group")
        self.action_configure_group.triggered.connect(self._configure_group)

        self.lbl_group_name.setText(group_name)

        self.lbl_status.linkActivated.connect(self._status_link_clicked)
        self.btn_start.clicked.connect(self._start_recording)
        self.lbl_duration.clicked.connect(self._configure_group)
        self.timer.timeout.connect(self._update_timer)

    def show_group_name(self):
        self.lbl_group_name.setVisible(True)

    def hide_group_name(self):
        self.lbl_group_name.setVisible(False)

    def request_active_session(self):
        self.active_session_requested.emit(self.group_id)

    @Slot(object)
    def group_changed(self, group_config: GroupConfig):
        if self.group_id != group_config.id:
            return
        self.group_name = group_config.name
        self._update_lbl_group_name()

    def set_active_session(self, group_id: str, session_id: str, state: SessionStateBase):
        if group_id != self.group_id:
            return

        print(f"Active session changed for group {group_id}: {session_id}")

        self.session_id = session_id
        self.set_session_state(group_id, session_id, state)

    def set_session_state(self, group_id: str, session_id: str, state: SessionStateBase):
        if group_id != self.group_id or session_id != self.session_id:
            return

        self.state = state
        self._update_lbl_status()
        self._update_lbl_group_name()
        self._update_btn_start()
        self._update_lbl_duration()

        if isinstance(state, Running) and not isinstance(state, AcquisitionFinished):
            self._ensure_timer_running(state.start_time)
        elif isinstance(state, AcquisitionFinished):
            print("Acquisition finished, stopping timer")
            self._stop_timer(state.stop_time)
        else:
            self._stop_timer()

    def _update_btn_start(self):
        enabled = self.session_id is not None and isinstance(self.state, (Ready, Running))
        self.btn_start.setEnabled(enabled)

        if isinstance(self.state, Running):
            self.btn_start.setText("Stop")
        else:
            self.btn_start.setText("Start")

    def _update_lbl_group_name(self):
        group_name = self.group_name or ""
        self.lbl_group_name.setText(f"{group_name} - Recording #{self.state.recording_number}")
            
    def _update_lbl_status(self):
        if isinstance(self.state, Ready):
            #self.lbl_status.setText("Ready - <a href=\"fill_placeholders\">Edit Information</a>")
            self.lbl_status.setText("Ready")
            self.lbl_status.setStyleSheet("QLabel { color: black; }")
        elif isinstance(self.state, Started):
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
        self.start_time = start_time

        if not self.timer.isActive():
            self.timer.start(100)  # Update 10 times a second

    def _stop_timer(self, stop_time: Optional[datetime] = None):
        self.timer.stop()
        if stop_time is None or self.start_time is None:
            self.lbl_recording_time.setText("0:00:00")
            self.start_time = None
            return

        elapsed = stop_time - self.start_time
        time_str = str(elapsed).split(".")[0]  # Format as HH:MM:SS
        self.lbl_recording_time.setText(time_str)

    def _update_timer(self):
        assert self.start_time is not None
        elapsed = datetime.now() - self.start_time
        if self.state.duration is not None:
            if elapsed.total_seconds() > self.state.duration:
                self._stop_recording()
        time_str = str(elapsed).split(".")[0]  # Format as HH:MM:SS
        self.lbl_recording_time.setText(time_str)

    def _update_lbl_duration(self):
        if self.state.duration is not None:
            duration = timedelta(seconds=self.state.duration)
            duration_str = f"/ {str(duration).split('.')[0]}"
        else:
            duration_str = "/ -:--:--"
        self.lbl_duration.setText(duration_str)

    def _configure_group(self):
        print("Configure Group")
        self.edit_group.emit(self.group_id)

    def _start_recording(self):
        if not self.session_id:
            return
        if isinstance(self.state, Running):
            if self.state.duration is not None and not self._confirm_stop_recording():
                return
            self.recording_stop.emit(self.group_id, self.session_id)
        else:
            self.recording_start.emit(self.group_id, self.session_id)

    def _confirm_stop_recording(self):
        reply = QMessageBox.question(self, "Confirm Stop Recording", "The recording has a set duration and is not finished yet. Are you sure you want to stop it?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def _stop_recording(self):
        if not self.session_id:
            return
        self.recording_stop.emit(self.group_id, self.session_id)

    def _status_link_clicked(self, link: str):
        self.goto.emit([link])

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())
