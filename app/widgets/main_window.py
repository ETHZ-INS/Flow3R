from concurrent.futures import Future
from copy import deepcopy
from pathlib import Path
from typing import List

from PySide6 import QtWidgets
from PySide6.QtCore import QByteArray
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
from app.widgets.pipeline_configuration_dialog import PipelineConfigurationDialog
from app.widgets.recording_controls_widget import RecordingControlsWidgetFactory
from app.widgets.variable_edit_dialog import VariableEditDialog
from app.widgets.variable_list_dialog import VariableListDialog
from app.widgets.variable_preparation_dialog import VariablePreparationDialog


class WelfareRecorder(Ui_WelfareRecorder, QMainWindow):
    def __init__(self, config_file: Path = None):
        super(WelfareRecorder, self).__init__()

        self.setupUi(self)
        self.setStyleSheet("QPushButton:disabled {color: gray}")

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

        self.action_add_camera_group.triggered.connect(self.add_camera_group)
        self.action_configure_camera_groups.triggered.connect(self.configure_camera_groups)

        self.action_add_variable.triggered.connect(self.add_variable)
        self.action_configure_variables.triggered.connect(self.configure_variables)

        self.action_configure_pipelines.triggered.connect(self.configure_pipelines)

        if self.config_file:
            self.load_project(self.config_file)

    def add_camera(self):
        dialog = CameraEditDialog(self.controller)
        dialog.setWindowTitle("Add Camera")
        dialog.exec()

    def edit_camera(self, camera_id: str):
        camera_config = self.controller.config.cameras.get(camera_id)
        if camera_config is None:
            return

        dialog = CameraEditDialog(self.controller, camera_config=camera_config)
        dialog.setWindowTitle("Edit Camera")
        dialog.exec()

    def add_camera_group(self):
        dialog = CameraGroupEditDialog(self.controller)
        dialog.setWindowTitle("Add Camera Group")
        dialog.exec()

    def edit_camera_group(self, recording_id: str):
        group_config = self.controller.config.groups.get(recording_id)
        if group_config is None:
            return

        dialog = CameraGroupEditDialog(self.controller, group_config=group_config)
        dialog.setWindowTitle("Edit Camera Group")
        dialog.exec()

    def configure_cameras(self):
        dialog = CameraListDialog(self.controller, parent=self)
        dialog.setWindowTitle("Configure Cameras")
        dialog.exec()

    def configure_camera_groups(self):
        dialog = CameraGroupListDialog(self.controller, parent=self)
        dialog.setWindowTitle("Configure Camera Groups")
        dialog.exec()

    def configure_pipelines(self, camera_id: str = None):
        dialog = PipelineConfigurationDialog(self.controller, selected_camera_id=camera_id, parent=self)
        dialog.setWindowTitle("Configure Pipelines")
        dialog.exec()

    def add_variable(self):
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

    def configure_variables(self):
        dialog = VariableListDialog(self.controller, parent=self)
        dialog.setWindowTitle("Configure Variables")
        dialog.exec()

        dialog = VariablePreparationDialog(self.controller, recording_id=list(self.controller.config.groups.values())[1].recording_id, parent=self)
        dialog.setWindowTitle("Prepare Variables")
        dialog.exec()

    def fill_variables_recording(self, recording_id: str):
        dialog = VariablePreparationDialog(self.controller, recording_id=recording_id, parent=self)
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

        self.controller.save_config.future(self.config_file, ui_state)

    def save_project_as(self):
        selected_file = self._select_save_file()
        if not selected_file:
            return
        self.config_file = selected_file
        self.save_project()

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

        res = future.result()

        if not res.success :
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load project: {res.message}")
            return

        ui_state = res.message
        self.restoreGeometry(QByteArray(ui_state["geometry"]))
        #self.restoreState(QByteArray(ui_state["window_state"]))
        self.dock_window.restoreGeometry(QByteArray(ui_state["dock_window_geometry"]))
        self.dock_window.restoreState(QByteArray(ui_state["dock_window_state"]))
