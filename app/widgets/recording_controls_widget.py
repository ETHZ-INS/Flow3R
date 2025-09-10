import time
from typing import TYPE_CHECKING

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenu, QLabel

from app.config.welfare_recorder_config import RecordingConfigView
from app.flow_layout import FlowLayout
from app.layout.recording_controls_widget import Ui_RecordingControlsWidget
from app.recording_state import RecordingStateBase, RecordingState
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
        widget.fill_variables.connect(lambda rid: self.ui.fill_variables_recording(recording_id=rid))

        widget.request_recording_state.connect(lambda rid: self.controller.check_recording_state.future(rid))

        self.controller.recording_view_changed.connect(widget.recording_view_changed)
        self.controller.recording_state_changed.connect(widget.recording_state_changed)

        self.controller.refresh_recording_view.future(recording_id)
        self.controller.check_recording_state.future(recording_id)

        return widget

    def update_widget(self, widget: "RecordingControlsWidget", config: dict) -> "RecordingControlsWidget":
        return widget


class RecordingControlsWidget(Ui_RecordingControlsWidget, QtWidgets.QFrame):
    recording_start = Signal(str)  # Signal to start recording
    recording_stop = Signal(str)   # Signal to stop recording

    edit_recording = Signal(str)  # Signal to configure recording
    fill_variables = Signal(str)  # recording_id, missing_placeholder_names

    request_recording_state = Signal(str)  # Signal to request recording state update

    def __init__(self, recording_id: str, recording_name: str = None, show_recording_name: bool = True, show_context_menu: bool = True, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        preview_layout = FlowLayout(self.frm_preview)
        self.frm_preview.setLayout(preview_layout)

        print("Initializing RecordingControlsWidget with recording_id:", recording_id)

        self.recording_id = recording_id
        self.recording_name = recording_name
        self.show_recording_name = show_recording_name
        self.show_context_menu = show_context_menu

        self.recording_view = None

        self.context_menu = QMenu(self)
        self.action_configure_recording = self.context_menu.addAction("Configure Recording")
        self.action_configure_recording.triggered.connect(self._configure_recording)

        self.lbl_status.linkActivated.connect(self._status_link_clicked)

        self.recording_state = RecordingState.NotReady()

        self.btn_start.clicked.connect(self._start_recording)

        self.update_all()

    @thread_bound(timeout_ms=2000)
    def set_recording_id(self, recording_id: str, recording_name: str):
        print("Setting recording ID:", recording_id)
        if self.recording_id == recording_id:
            return

        self.recording_id = recording_id
        self.recording_name = recording_name

        self.request_recording_state.emit(self.recording_id)

        self.update_all()

    @thread_bound(timeout_ms=2000)
    def set_recording_time(self, recording_time: float):
        time_str = time.strftime("%H:%M:%S", time.gmtime(recording_time))
        self.lbl_recording_time.setText(time_str)

    def update_lbl_recording_name(self):
        if self.show_recording_name and self.recording_name is not None:
            self.lbl_recording_name.setText(self.recording_name)
            self.lbl_recording_name.show()
        else:
            self.lbl_recording_name.hide()

    def update_btn_start(self):
        enabled = self.recording_id is not None and isinstance(self.recording_state, (RecordingState.Ready, RecordingState.Running))
        self.btn_start.setEnabled(enabled)

        if isinstance(self.recording_state, RecordingState.Running):
            self.btn_start.setText("Stop")
        else:
            self.btn_start.setText("Start")

    def update_lbl_status(self):
        if isinstance(self.recording_state, RecordingState.Ready):
            self.lbl_status.setText("Ready - <a href=\"fill_variables\">Edit Information</a>")
            self.lbl_status.setStyleSheet("QLabel { color: black; }")
        elif isinstance(self.recording_state, RecordingState.Running):
            self.lbl_status.setText("Recording...")
            self.lbl_status.setStyleSheet("QLabel { color: green; }")
        elif isinstance(self.recording_state, RecordingState.NotReady):
            if isinstance(self.recording_state, RecordingState.MissingInfo):
                self.lbl_status.setText("Not Ready: <a href=\"fill_variables\">Missing Information</a>")
            else:
                self.lbl_status.setText(f"Not Ready: {self.recording_state.reason}")
            self.lbl_status.setStyleSheet("QLabel { color: red; }")
        elif isinstance(self.recording_state, RecordingState.Error):
            if isinstance(self.recording_state, RecordingState.InvalidPlaceholders):
                self.lbl_status.setText(f"Error: invalid placeholders: {', '.join(self.recording_state.invalid_placeholders)}")
            else:
                self.lbl_status.setText(f"Error: {self.recording_state.message}")
            self.lbl_status.setStyleSheet("QLabel { color: red; }")
        else:
            self.lbl_status.setText("")
            self.lbl_status.setStyleSheet("QLabel { color: black; }")

    def update_frm_preview(self):
        self.frm_preview.layout().clear()

        if self.recording_view is None or not any(placeholder.show_in_controls for placeholder in self.recording_view.placeholders):
            self.frm_preview.hide()
            return

        self.frm_preview.show()

        for placeholder in self.recording_view.placeholders:
            if not placeholder.show_in_controls:
                continue

            if placeholder.scope == "camera" and len(self.recording_view.camera_views) > 1:
                for camera_view in self.recording_view.camera_views:
                    placeholder_context = camera_view.get_placeholder_context()
                    value = placeholder_context.resolve(placeholder.variable_name)
                    if value.missing_dependencies:
                        continue

                    if value.is_set:
                        value = value.value
                    else:
                        value = "(not set)"
                    lbl = QLabel(f"{placeholder.variable_label} ({camera_view.camera.camera_name}) - {value}")
                    lbl.setTextFormat(QtCore.Qt.TextFormat.RichText)
                    lbl.setStyleSheet("background: lightblue; padding: 5px; border: 1px solid gray; border-radius: 5px;")
                    self.frm_preview.layout().addWidget(lbl)
            else:
                camera_view = self.recording_view.camera_views[0]
                placeholder_context = camera_view.get_placeholder_context()
                value = placeholder_context.resolve(placeholder.variable_name)
                if value.missing_dependencies:
                    continue

                if value.is_set and not value.missing_dependencies:
                    value = value.value
                else:
                    value = "(not set)"
                lbl = QLabel(f"{placeholder.variable_label} - {value}")
                lbl.setTextFormat(QtCore.Qt.TextFormat.RichText)
                lbl.setStyleSheet("background: lightblue; padding: 5px; border: 1px solid gray; border-radius: 5px;")
                self.frm_preview.layout().addWidget(lbl)

    def update_all(self):
        self.update_lbl_recording_name()
        self.update_btn_start()
        self.update_lbl_status()
        self.update_frm_preview()

    def _start_recording(self):
        if isinstance(self.recording_state, RecordingState.Running):
            self.recording_stop.emit(self.recording_id)
        else:
            self.recording_start.emit(self.recording_id)

    def _configure_recording(self):
        self.edit_recording.emit(self.recording_id)

    def _status_link_clicked(self, link: str):
        if link == "fill_variables":
            self.fill_variables.emit(self.recording_id)

    def recording_view_changed(self, recording_id: str, recording_view: RecordingConfigView):
        if self.recording_id != recording_id:
            return

        self.recording_view = recording_view

        if recording_view.recording.recording_name != self.recording_name:
            self.recording_name = recording_view.recording.recording_name
            self.update_lbl_recording_name()

        #if recording_view.placeholders != self.recording_view.placeholders:
        #    self.update_frm_preview()
        self.update_frm_preview()

    def recording_state_changed(self, recording_id: str, recording_state: RecordingStateBase):
        if self.recording_id != recording_id:
            return

        if self.recording_state != recording_state:
            self.recording_state = recording_state
            self.update_all()

    def contextMenuEvent(self, event):
        if not self.show_context_menu:
            super().contextMenuEvent(event)
            return
        self.context_menu.exec(event.globalPos())
