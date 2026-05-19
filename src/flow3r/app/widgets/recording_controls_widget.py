from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QInputDialog, QMenu, QWidget, QMessageBox, QLabel, QSizePolicy

from flow3r.app.config.group_config import GroupConfig
from flow3r.app.layout.recording_controls_widget import Ui_RecordingControlsWidget
from flow3r.app.controller.session_state import SessionStateBase, Ready, Running, AcquisitionFinished, \
    FinishingProcessing, \
    FinishingRecording, NotReady, MissingPlaceholder, Error, ConfigError, InvalidPlaceholders, Started, StartFailed


class ElidingLabel(QLabel):
    """A single-line QLabel that elides text with '…' and shows the full text as a tooltip."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._full_text = ""
        self._is_rich_text = False
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)

    def setFullText(self, text: str):
        self._full_text = " ".join(text.splitlines())
        self._is_rich_text = "<" in text  # simple heuristic for HTML content
        if self._is_rich_text:
            self.setToolTip("")
            super().setText(text)
        else:
            self.setToolTip(text)
            self._elide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._is_rich_text:
            self._elide()

    def _elide(self):
        fm = self.fontMetrics()
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, self.width())
        super().setText(elided)


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setStyleSheet("color: grey;")

    def enterEvent(self, event):
        if self.isEnabled():
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.setStyleSheet("color: grey; text-decoration: underline;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.setStyleSheet("color: grey;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.isEnabled() and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class RecordingControlsWidget(Ui_RecordingControlsWidget, QWidget):
    recording_start = Signal(str, str)  # group_id, session_id
    recording_stop = Signal(str, str)  # group_id, session_id
    open_placeholder_dialog_for_start = Signal(str, str)  # group_id, session_id

    active_session_requested = Signal(str)

    edit_group = Signal(str)  # group_id
    set_placeholder_values = Signal(str)  # group_id
    set_recording_number = Signal(str, int)  # group_id, number

    def __init__(self, group_id: str, group_name: str, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.frm_preview.setVisible(False)
        self.lbl_recording_time.setText("0:00:00")

        # Replace the generated lbl_status with an ElidingLabel
        layout = self.lbl_status.parent().layout()
        index = layout.indexOf(self.lbl_status)
        self.lbl_status.deleteLater()
        self.lbl_status = ElidingLabel(parent=self)
        self.lbl_status.setMinimumWidth(50)
        self.lbl_status.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        layout.insertWidget(index, self.lbl_status)

        self.lbl_duration.deleteLater()
        self.lbl_duration = ClickableLabel(text="/ -:--:--", parent=self.frm_controls)
        self.lbl_duration.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        self.frm_controls.layout().addWidget(self.lbl_duration)
        self.lbl_duration.setToolTip("Click to configure recording duration")

        # Replace lbl_group_name with a header row:
        #   static group-name label  +  clickable recording-number label
        vlayout = self.lbl_group_name.parent().layout()
        header_idx = vlayout.indexOf(self.lbl_group_name)
        self.lbl_group_name.deleteLater()

        header_frame = QFrame(self)
        header_frame.setFrameShape(QFrame.Shape.NoFrame)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        self.lbl_group_name = QLabel(parent=header_frame)
        header_layout.addWidget(self.lbl_group_name)

        self.lbl_recording_number = ClickableLabel(parent=header_frame)
        self.lbl_recording_number.setToolTip("Click to change recording number")
        header_layout.addWidget(self.lbl_recording_number)
        header_layout.addStretch()

        vlayout.insertWidget(header_idx, header_frame)

        self.group_id = group_id
        self.group_name: Optional[str] = group_name
        self.session_id: Optional[str] = None
        self.state: SessionStateBase = NotReady(recording_number=0)
        self._pending_auto_start: bool = False

        self.start_time: Optional[datetime] = None
        self.timer = QTimer(self)

        self.context_menu = QMenu(self)
        self.action_configure_group = self.context_menu.addAction("Configure Group")
        self.action_configure_group.triggered.connect(self._configure_group)

        self.lbl_group_name.setText(group_name)
        self.lbl_recording_number.setText("- Recording #0")

        self.lbl_status.linkActivated.connect(self._status_link_clicked)
        self.btn_start.clicked.connect(self._start_recording)
        self.lbl_duration.clicked.connect(self._configure_group)
        self.lbl_recording_number.clicked.connect(self._recording_number_clicked)
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
        if session_id != self.session_id:
            self._pending_auto_start = False
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
            self._stop_timer(state.stop_time)
        else:
            self._stop_timer()

        if self._pending_auto_start:
            if isinstance(self.state, (Ready, StartFailed)):
                self._pending_auto_start = False
                self._start_recording()
            else:
                # Unexpected state — cancel the pending flag rather than leaving it stuck.
                self._pending_auto_start = False

    def _update_btn_start(self):
        enabled = self.session_id is not None and isinstance(
            self.state, (Ready, StartFailed, Running, MissingPlaceholder)
        )
        self.btn_start.setEnabled(enabled)

        if isinstance(self.state, Running):
            self.btn_start.setText("Stop")
        elif isinstance(self.state, MissingPlaceholder):
            self.btn_start.setText("Start\u2026")  # ellipsis signals a dialog will open first
        else:
            self.btn_start.setText("Start")

    def _update_lbl_group_name(self):
        self.lbl_group_name.setText(self.group_name or "")
        self.lbl_recording_number.setText(f"- Recording #{self.state.recording_number}")
        self.lbl_recording_number.setEnabled(not isinstance(self.state, Running))

    def _update_lbl_status(self):
        if isinstance(self.state, Ready):
            self.lbl_status.setFullText("Ready - <a href=\"fill_placeholders\">Edit Placeholders</a>")
            self.lbl_status.setStyleSheet("QLabel { color: black; }")
        elif isinstance(self.state, StartFailed):
            self.lbl_status.setFullText(f"Start failed: {self.state.message}")
            self.lbl_status.setStyleSheet("QLabel { color: red; }")
        elif isinstance(self.state, Started):
            if isinstance(self.state, FinishingProcessing):
                self.lbl_status.setFullText(f"Finishing processing ({self.state.processing_progress*100:.0f}%)...")
                self.lbl_status.setStyleSheet("QLabel { color: orange; }")
            elif isinstance(self.state, FinishingRecording):
                self.lbl_status.setFullText("Finishing recording...")
                self.lbl_status.setStyleSheet("QLabel { color: green; }")
            else:
                self.lbl_status.setFullText("Recording...")
                self.lbl_status.setStyleSheet("QLabel { color: green; }")
        elif isinstance(self.state, NotReady):
            if isinstance(self.state, MissingPlaceholder):
                self.lbl_status.setFullText("Almost Ready: <a href=\"fill_placeholders\">Missing Information</a>")
                self.lbl_status.setStyleSheet("QLabel { color: orange; }")
            else:
                self.lbl_status.setFullText(f"Not Ready: {self.state.reason}")
                self.lbl_status.setStyleSheet("QLabel { color: red; }")
        elif isinstance(self.state, Error):
            if isinstance(self.state, ConfigError):
                self.lbl_status.setFullText(f"Config Error: <a href=\"config_error\">{self.state.message}</a>")
            elif isinstance(self.state, InvalidPlaceholders):
                self.lbl_status.setFullText(f"Error: invalid placeholders: {', '.join(self.state.invalid_placeholders)}")
            else:
                self.lbl_status.setFullText(f"Error: {self.state.message}")
            self.lbl_status.setStyleSheet("QLabel { color: red; }")
        else:
            self.lbl_status.setFullText("")
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
        self.edit_group.emit(self.group_id)

    def trigger_start_stop(self):
        """Public entry point for keyboard shortcuts — behaves identically to clicking Start/Stop."""
        self._start_recording()

    @Slot(str, str)
    def on_auto_start_requested(self, group_id: str, session_id: str) -> None:
        """Set the pending-auto-start flag when the placeholder dialog requests a start.

        The actual start (including the file-overwrite confirmation) is deferred until
        ``set_session_state`` delivers a ``Ready`` or ``StartFailed`` state — i.e. after
        the placeholder values committed by the dialog have been processed by the worker
        thread and the resolved file paths are available for the overwrite check.
        """
        if group_id == self.group_id and session_id == self.session_id:
            self._pending_auto_start = True

    def _start_recording(self):
        if not self.session_id:
            return

        if isinstance(self.state, Running):
            if self.state.duration is not None and not self._confirm_stop_recording():
                return
            self.recording_stop.emit(self.group_id, self.session_id)
        elif isinstance(self.state, MissingPlaceholder):
            self.open_placeholder_dialog_for_start.emit(self.group_id, self.session_id)
        else:
            files_that_will_be_overwritten = []
            if isinstance(self.state, (Ready, StartFailed)):
                files = self.state.files
                for file in files:
                    if file.exists():
                        files_that_will_be_overwritten.append(file)

            if files_that_will_be_overwritten:
                file_list_str = "\n".join(str(file) for file in files_that_will_be_overwritten)
                reply = QMessageBox.question(self, "Confirm Start Recording", f"The following files already exist and will be overwritten:\n{file_list_str}\nDo you want to continue?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return

            self.recording_start.emit(self.group_id, self.session_id)

    def _confirm_stop_recording(self):
        reply = QMessageBox.question(self, "Confirm Stop Recording", "The recording has a set duration and is not finished yet. Are you sure you want to stop it?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def _stop_recording(self):
        if not self.session_id:
            return
        self.recording_stop.emit(self.group_id, self.session_id)

    def _status_link_clicked(self, link: str):
        if link == "fill_placeholders":
            self.set_placeholder_values.emit(self.group_id)

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())

    def _recording_number_clicked(self):
        menu = QMenu(self)
        action_reset = menu.addAction("Reset to 1")
        action_set = menu.addAction("Set to specific number…")
        action = menu.exec(QCursor.pos())
        if action == action_reset:
            self.set_recording_number.emit(self.group_id, 1)
        elif action == action_set:
            value, ok = QInputDialog.getInt(
                self,
                "Set Recording Number",
                "Recording number:",
                self.state.recording_number,
                1,
                99999,
            )
            if ok:
                self.set_recording_number.emit(self.group_id, value)
