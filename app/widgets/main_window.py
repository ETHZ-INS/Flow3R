from concurrent.futures import Future
from pathlib import Path
from datetime import datetime
from typing import List

from PySide6 import QtWidgets
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import  QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QMainWindow, QFileDialog

from app.layout.main_window import Ui_WelfareRecorder
from app.controller import Controller
from app.recording.widget_manager import WidgetManager
from app.thread_bound_callable import thread_bound
from app.widgets.camera_edit_dialog import CameraEditDialog
from app.widgets.camera_group_edit_dialog import CameraGroupEditDialog
from app.widgets.camera_group_list_dialog import CameraGroupListDialog
from app.widgets.camera_list_dialog import CameraListDialog
from app.widgets.camera_widget import CameraWidgetFactory
from app.widgets.pipeline_edit_dialog import PipelineEditDialog
from app.widgets.pipeline_list_dialog import PipelineListDialog
from app.widgets.recording_controls_widget import RecordingControlsWidgetFactory
from app.widgets.variable_edit_dialog import VariableEditDialog
from app.widgets.variable_list_dialog import VariableListDialog
from app.widgets.variable_preparation_dialog import VariablePreparationDialog


LOG_COLORS = {
    "INFO": QColor("black"),
    "WARNING": QColor("orange"),
    "ERROR": QColor("red"),
}


class MainWindow(Ui_WelfareRecorder, QMainWindow):
    def __init__(self, config_file: Path = None):
        super(MainWindow, self).__init__()

        self.setupUi(self)
        self.setStyleSheet("QPushButton:disabled {color: gray}")

        self.su_mode = False

        inner = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(inner)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        # To make docked widgets take up the full height, we add an inner MainWindow instance
        # Don't ask me why it works like that, but it does
        self.dock_window = QMainWindow(self.frm_dock_window)
        self.dock_window.setDockNestingEnabled(True)

        vbox.addWidget(self.dock_window)
        vbox.addWidget(self.frm_recordings)
        vbox.addWidget(self.frm_footer)

        self.setCentralWidget(inner)

        self.txt_log.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.txt_log.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # ensure arrow, not I-beam
        self.txt_log.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.txt_log.document().setMaximumBlockCount(200)

        self.widget_manager = WidgetManager(self.dock_window, self.frm_recordings)
        self.controller = Controller(self.widget_manager)

        self.widget_manager.register_widget_type("camera", CameraWidgetFactory(self.controller, self))
        self.widget_manager.register_widget_type("recording_controls", RecordingControlsWidgetFactory(self.controller, self))

        self.config_file = config_file

        self.action_save_project.triggered.connect(self.save_project)
        self.action_save_project_as.triggered.connect(self.save_project_as)
        self.action_load_project.triggered.connect(self.load_project)

        self.action_add_camera.triggered.connect(self.add_camera)
        self.action_configure_cameras.triggered.connect(self.configure_cameras)

        self.action_add_pipeline.triggered.connect(self.add_pipeline)
        self.action_configure_pipelines.triggered.connect(self.configure_pipelines)

        self.action_add_camera_group.triggered.connect(self.add_camera_group)
        self.action_configure_camera_groups.triggered.connect(self.configure_camera_groups)

        self.action_add_placeholder.triggered.connect(self.add_placeholder)
        self.action_configure_placeholders.triggered.connect(self.configure_placeholders)

        self.action_enable_superuser_mode.triggered.connect(self.enable_su_mode)

        self.controller.log_message_added.connect(self.add_log_entry)

        if self.config_file:
            self.load_project(self.config_file)

        self.add_log_entry("Application started", "INFO")

    def enable_su_mode(self):
        self.su_mode = True
        self.setWindowTitle("Flow3R (Superuser Mode)")
        self.action_enable_superuser_mode.setEnabled(False)

    def add_log_entry(self, message: str, level: str = "INFO"):
        edit = self.txt_log
        sb = edit.verticalScrollBar()
        stick = (sb.value() == sb.maximum())

        cursor = edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # new line BEFORE the entry, not after the previous one
        if not edit.document().isEmpty():
            cursor.insertBlock()

        fmt = QTextCharFormat()
        fmt.setForeground(LOG_COLORS.get(level, QColor("black")))

        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor.insertText(f"{timestamp} [{level}] {message}", fmt)

        edit.setTextCursor(cursor)

        # snap to bottom only if user was already at bottom
        if stick:
            sb.setValue(sb.maximum())

    def goto(self, location: List[str]):
        if len(location) < 2:
            return

        if location[0] == "camera":
            self.edit_camera(location[1])
        elif location[0] == "pipeline":
            self.edit_pipeline(location[1], location[2:])
        elif location[0] == "camera_group":
            self.edit_camera_group(location[1])
        elif location[0] == "variable":
            self.edit_variable(location[1])
        #elif location[0] == "prepare_variables":
        #    self.fill_variables_recording(location[1])


    def add_camera(self):
        dialog = CameraEditDialog(self.controller, su_mode=self.su_mode, parent=self)
        dialog.setWindowTitle("Add Camera")
        dialog.exec()

    def edit_camera(self, camera_id: str):
        config = self.controller.get_config()
        camera = config.cameras.get(camera_id)
        if camera is None:
            return

        dialog = CameraEditDialog(self.controller, camera_config=camera, su_mode=self.su_mode, parent=self)
        dialog.setWindowTitle("Edit Camera")
        dialog.exec()

    def add_pipeline(self):
        dialog = PipelineEditDialog(self.controller, su_mode=self.su_mode, parent=self)
        dialog.setWindowTitle("Add Pipeline")
        dialog.exec()

    def edit_pipeline(self, pipeline_id: str, location: List[str] = None):
        config = self.controller.get_config()
        pipeline = config.pipelines.get(pipeline_id)
        if pipeline is None:
            return

        dialog = PipelineEditDialog(self.controller, pipeline=pipeline, location=location, parent=self)
        dialog.setWindowTitle("Edit Pipeline")
        dialog.exec()

    def add_camera_group(self):
        dialog = CameraGroupEditDialog(self.controller)
        dialog.setWindowTitle("Add Camera Group")
        dialog.exec()

    def edit_camera_group(self, group_id: str):
        config = self.controller.get_config()
        group = config.groups.get(group_id)
        if group is None:
            return

        dialog = CameraGroupEditDialog(self.controller, group=group)
        dialog.setWindowTitle("Edit Camera Group")
        dialog.exec()

    def configure_cameras(self):
        dialog = CameraListDialog(self.controller, su_mode=self.su_mode, parent=self)
        dialog.setWindowTitle("Configure Cameras")
        dialog.exec()

    def configure_pipelines(self):
        dialog = PipelineListDialog(self.controller, parent=self)
        dialog.setWindowTitle("Configure Pipelines")
        dialog.exec()

    def configure_camera_groups(self):
        dialog = CameraGroupListDialog(self.controller, su_mode=self.su_mode, parent=self)
        dialog.setWindowTitle("Configure Camera Groups")
        dialog.exec()

    def add_placeholder(self):
        dialog = VariableEditDialog(self.controller)
        dialog.setWindowTitle("Add Variable")
        dialog.exec()

    def edit_variable(self, variable_id: str):
        variable_config = self.controller.config.variables.get(variable_id)
        if variable_config is None:
            return

        dialog = VariableEditDialog(self.controller, variable_config=variable_config)
        dialog.setWindowTitle("Edit Variable")
        dialog.exec()

    def configure_placeholders(self):
        dialog = VariableListDialog(self.controller, parent=self)
        dialog.setWindowTitle("Configure Variables")
        dialog.exec()

    def fill_variables_recording(self, group_id: str):
        dialog = VariablePreparationDialog(self.controller, group_id=group_id, parent=self)
        dialog.setWindowTitle("Prepare Variables")
        dialog.exec()

    def _select_save_file(self):
        if self.config_file is None:
            # Default path when opening the file dialog
            selected_file = str(Path.home() / "project.wrc")
        else:
            selected_file = str(self.config_file)

        file_filter = "Welfare Recorder Config Files (*.wrc)"
        selected_file, _ = QFileDialog.getSaveFileName(self, "Save Project", selected_file, file_filter)

        return Path(selected_file) if selected_file else None

    def _select_load_file(self):
        if self.config_file is None:
            # Default path when opening the file dialog
            directory = str(Path.home())
        else:
            directory = str(self.config_file)

        file_filter = "Welfare Recorder Config Files (*.wrc)"
        selected_file, _ = QFileDialog.getOpenFileName(self, "Load Project", directory, file_filter)

        return Path(selected_file) if selected_file else None

    def save_project(self):
        if self.config_file is None:
            self.save_project_as()
            return

        geometry = self.saveGeometry()
        window_state = self.saveState()

        dock_window_geometry = self.dock_window.saveGeometry()
        dock_window_state = self.dock_window.saveState()

        ui_state = {
            "geometry": bytes(geometry),
            "window_state": bytes(window_state),
            "dock_window_geometry": bytes(dock_window_geometry),
            "dock_window_state": bytes(dock_window_state)
        }

        fut = self.controller.save_config.future(self.config_file, ui_state, self.su_mode)
        fut.add_done_callback(self._save_project_result.future)

    def save_project_as(self):
        selected_file = self._select_save_file()
        if not selected_file:
            return
        self.config_file = selected_file
        self.save_project()

    @thread_bound(timeout_ms=2000)
    def _save_project_result(self, future: Future):
        if future.exception() is not None:
            QtWidgets.QMessageBox.critical(self, "Error saving project", f"Failed to save project: {future.exception()}")
            return

    def load_project(self, config_file: Path = None):
        if config_file:
            selected_file = config_file
        else:
            selected_file = self._select_load_file()
            if not selected_file:
                return
        self.config_file = selected_file
        fut = self.controller.load_config.future(selected_file)
        fut.add_done_callback(self._project_loaded.future)

    @thread_bound(timeout_ms=2000)
    def _project_loaded(self, future: Future):
        if future.exception() is not None:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load project: {future.exception()}")
            return

        ui_state = future.result()
        self.restoreGeometry(QByteArray(ui_state["geometry"]))
        #self.restoreState(QByteArray(ui_state["window_state"]))
        self.dock_window.restoreGeometry(QByteArray(ui_state["dock_window_geometry"]))
        self.dock_window.restoreState(QByteArray(ui_state["dock_window_state"]))
