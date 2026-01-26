from typing import Optional

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QMenu, QWidget, QFrame

from aaaflow3r.app.layout.recording_controls_widget import Ui_RecordingControlsWidget


class RecordingControlsWidget(Ui_RecordingControlsWidget, QWidget):
    recording_start = Signal(str, str)  # group_id, session_id
    recording_stop = Signal(str, int)  # group_id, session_id
    recording_detach = Signal(str, int)  # group_id, session_id

    goto = Signal(list)  # Signal to open a config dialog
    edit_group = Signal(str)  # group_id

    def __init__(self, group_id: str, group_name: str, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.group_id = group_id
        self.session_id: Optional[str] = None

        self.context_menu = QMenu(self)
        self.action_configure_group = self.context_menu.addAction("Configure Group")
        self.action_configure_group.triggered.connect(self._configure_group)

        self.lbl_group_name.setText(group_name)

        self.lbl_status.linkActivated.connect(self._status_link_clicked)
        self.btn_start.clicked.connect(self._start_recording)

    def _configure_group(self):
        self.edit_group.emit(self.group_id)

    def _start_recording(self):
        if not self.session_id:
            return
        self.recording_start.emit(self.group_id, self.session_id)

    def _status_link_clicked(self, link: str):
        self.goto.emit([link])

    @Slot(object)
    def _group_config_changed(self, group_config):
        self.lbl_group_name.setText(group_config.name)

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())
