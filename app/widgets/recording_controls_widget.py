import time
from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenu

from app.layout.recording_controls_widget import Ui_RecordingControlsWidget
from app.thread_bound_callable import thread_bound

if TYPE_CHECKING:
    from app.controller import Controller
    from app.widgets.main_window import WelfareRecorder


class RecordingControlsWidgetFactory:
    def __init__(self, controller: "Controller", ui: "WelfareRecorder"):
        self.controller = controller
        self.ui = ui

    def create_widget(self, config: dict) -> "RecordingControlsWidget":
        recording_id = config["recording_id"]
        recording_name = config.get("recording_name", None)

        widget = RecordingControlsWidget(recording_id, recording_name)
        widget.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)

        widget.recording_start.connect(lambda rid: self.controller.start_recording.future(rid))
        widget.recording_stop.connect(lambda rid: self.controller.stop_recording.future(rid))

        widget.edit_recording.connect(self.ui.edit_camera_group)

        self.controller.recording_name_changed.connect(widget._recording_name_changed)
        self.controller.recording_state_changed.connect(widget._recording_state_changed)

        return widget

    def update_widget(self, widget: "RecordingControlsWidget", config: dict) -> "RecordingControlsWidget":
        return widget


class RecordingControlsWidget(Ui_RecordingControlsWidget, QtWidgets.QFrame):
    recording_start = Signal(str)  # Signal to start recording
    recording_stop = Signal(str)   # Signal to stop recording

    edit_recording = Signal(str)  # Signal to configure recording

    def __init__(self, recording_id: str, recording_name: str = None, show_recording_name: bool = True, show_context_menu: bool = True, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        print("Initializing RecordingControlsWidget with recording_id:", recording_id)

        self.recording_id = recording_id
        self.recording_name = recording_name
        self.show_recording_name = show_recording_name
        self.show_context_menu = show_context_menu

        self.context_menu = QMenu(self)
        self.action_configure_recording = self.context_menu.addAction("Configure Recording")
        self.action_configure_recording.triggered.connect(self._configure_recording)

        self.recording_running = False

        self.btn_start.clicked.connect(self._start_recording)

        self._update()

    @thread_bound(timeout_ms=2000)
    def set_recording_id(self, recording_id: str, recording_name: str):
        print("Setting recording ID:", recording_id)
        if self.recording_id == recording_id:
            return

        self.recording_id = recording_id
        self.recording_name = recording_name
        self._update()

    @thread_bound(timeout_ms=2000)
    def set_recording_time(self, recording_time: float):
        time_str = time.strftime("%H:%M:%S", time.gmtime(recording_time))
        self.lbl_recording_time.setText(time_str)

    def _update(self):
        print("Recording ID:", self.recording_id)
        if self.recording_name and self.show_recording_name:
            self.lbl_recording_name.setText(self.recording_name)
            self.lbl_recording_name.setVisible(True)
        else:
            self.lbl_recording_name.setVisible(False)

        if self.recording_id is None:
            self.btn_start.setEnabled(False)
            self.lbl_status.setText("Recording ID not set")
            self.lbl_recording_time.setText("00:00:00")
            return

        self.btn_start.setEnabled(True)
        if self.recording_running:
            self.btn_start.setText("Stop")
        else:
            self.btn_start.setText("Start")


    def _start_recording(self):
        if self.recording_running:
            self.recording_stop.emit(self.recording_id)
        else:
            self.recording_start.emit(self.recording_id)

    def _configure_recording(self):
        self.edit_recording.emit(self.recording_id)

    def _recording_name_changed(self, recording_id: str, recording_name: str):
        if self.recording_id != recording_id:
            return

        self.recording_name = recording_name
        self._update()

    def _recording_state_changed(self, recording_id: str, recording_state: str):
        if self.recording_id != recording_id:
            return

        if recording_state == "started":
            print("Enabling start button for started state")
            self.recording_running = True
            self.lbl_status.setText("Recording...")
            self.lbl_status.setStyleSheet("QLabel { color: green; }")
        elif recording_state == "stopped":
            print("Enabling start button for stopped state")
            self.lbl_status.setText("")
            self.recording_running = False

        self._update()

    def contextMenuEvent(self, event):
        if not self.show_context_menu:
            super().contextMenuEvent(event)
            return
        self.context_menu.exec(event.globalPos())
