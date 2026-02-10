from copy import deepcopy
from datetime import datetime

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QColor, Qt, QTextCursor, QTextCharFormat
from PySide6.QtWidgets import QMainWindow, QDialog

from aaaflow3r.app.api.plugins.plugins import PluginAPI
from aaaflow3r.app.config.app_config import AppConfig
from aaaflow3r.app.config.group_config import GroupConfig
from aaaflow3r.app.layout.main_window import Ui_WelfareRecorder
from aaaflow3r.app.controller import Controller
from aaaflow3r.app.widget_controller import WidgetController
from aaaflow3r.app.widget_service import WidgetService
from aaaflow3r.app.widgets.group_edit_dialog import GroupEditDialog
from aaaflow3r.app.widgets.group_list_dialog import GroupListDialog
from aaaflow3r.app.widgets.pipeline_config_dialog import PipelineConfigDialog
from aaaflow3r.app.widgets.pipeline_list_dialog import PipelineListDialog
from aaaflow3r.app.widgets.source_config_dialog import SourceConfigDialog
from aaaflow3r.app.widgets.source_list_dialog import SourceListDialog
from aaaflow3r.core.pipeline.pipeline_config import PipelineConfig
from aaaflow3r.core.source.source_config import SourceConfig


LOG_COLORS = {
    "INFO": QColor("black"),
    "WARNING": QColor("orange"),
    "ERROR": QColor("red"),
}


class MainWindow(Ui_WelfareRecorder, QMainWindow):
    source_added = Signal(object)  # source config
    source_edited = Signal(object)  # source config

    group_added = Signal(object)  # group config
    group_edited = Signal(object)  # group config

    pipeline_added = Signal(object)  # pipeline config
    pipeline_edited = Signal(object)  # pipeline config

    group_assigned_to_source = Signal(str, object)  # source_id, group_id
    pipeline_assigned_to_group = Signal(str, object)  # group_id, pipeline_id

    def __init__(self, plugin_api: PluginAPI, parent=None):
        super(MainWindow, self).__init__(parent)

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

        self.txt_log.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.txt_log.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # ensure arrow, not I-beam
        self.txt_log.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.txt_log.document().setMaximumBlockCount(200)

        self.plugin_api = plugin_api

        self.widget_controller = WidgetController(self.dock_window, self.frm_recordings)
        self.widget_service = WidgetService()
        self.widget_service.source_handle_added.connect(self.widget_controller.add_source_handle)
        self.widget_service.source_handle_removed.connect(self.widget_controller.remove_source_handle)
        self.widget_service.source_assignment_requested.connect(self.widget_controller.assign_source_handle)
        self.widget_service.source_widget_requested.connect(self.widget_controller.create_source_widget)
        self.widget_service.source_widget_released.connect(self.widget_controller.destroy_source_widget)

        self.widget_service.visualizer_handle_added.connect(self.widget_controller.add_visualizer_handle)
        self.widget_service.visualizer_handle_removed.connect(self.widget_controller.remove_visualizer_handle)
        self.widget_service.visualizer_assignment_requested.connect(self.widget_controller.assign_visualizer_handle)
        self.widget_service.visualizer_widget_requested.connect(self.widget_controller.create_visualizer_widget)
        self.widget_service.visualizer_widget_released.connect(self.widget_controller.destroy_visualizer_widget)

        self.widget_service.recording_controls_requested.connect(self.widget_controller.create_recording_controls_widget)
        self.widget_service.recording_controls_released.connect(self.widget_controller.remove_recording_controls_widget)
        self.widget_service.recording_controls_location_requested.connect(self.widget_controller.set_recording_controls_widget_location)

        self.controller = Controller(self.plugin_api.source_types.get_source_types(), self.plugin_api.pipeline_types.get_pipeline_types(), self.widget_service)
        self.widget_controller._main_window = self
        self.widget_controller.set_controller(self.controller)

        self.worker_thread = QThread()
        self.controller.moveToThread(self.worker_thread)
        self.worker_thread.setObjectName("SourceControllerThread")
        self.worker_thread.start()

        self.action_list_sources.triggered.connect(self._list_sources)
        self.action_list_groups.triggered.connect(self._list_groups)
        self.action_list_pipelines.triggered.connect(self._list_pipelines)

        self.action_add_source.triggered.connect(self._add_source)
        self.action_add_group.triggered.connect(self._add_group)
        self.action_add_pipeline.triggered.connect(self._add_pipeline)

        self.source_added.connect(self.controller.add_source)
        self.source_edited.connect(self.controller.edit_source)

        self.group_added.connect(self.controller.add_group)
        self.group_edited.connect(self.controller.edit_group)

        self.pipeline_added.connect(self.controller.add_pipeline)
        self.pipeline_edited.connect(self.controller.edit_pipeline)

        self.group_assigned_to_source.connect(self.controller.assign_group)
        self.pipeline_assigned_to_group.connect(self.controller.assign_pipeline)

        self.controller.log_message.connect(self.add_log_entry)
        self.controller.config_changed.connect(self._config_changed)

        self._config: AppConfig = deepcopy(self.controller.config)

        self.add_log_entry("Application started", "INFO")

    @Slot(str, str)
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

    def _list_sources(self):
        source_types = list(self.plugin_api.source_types.get_source_types().values())
        source_list_dialog = SourceListDialog(self.controller, source_types)
        source_list_dialog.setWindowTitle("Sources")
        source_list_dialog.exec()

    def _add_source(self):
        source_config = SourceConfig()
        source_types = list(self.plugin_api.source_types.get_source_types().values())
        dialog = SourceConfigDialog(source_types, source_config, self)
        dialog.setWindowTitle("Add source")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.source_added.emit(source_config)

    def _edit_source(self, source_id: str):
        source_config = self._config.sources.get(source_id)
        assert source_config is not None

        source_types = list(self.plugin_api.source_types.get_source_types().values())
        dialog = SourceConfigDialog(source_types, source_config, self)
        dialog.setWindowTitle("Edit source")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.source_edited.emit(source_config)

    def _list_groups(self):
        group_list_dialog = GroupListDialog(self.controller)
        group_list_dialog.setWindowTitle("Groups")
        group_list_dialog.exec()

    def _add_group(self):
        group_config = GroupConfig()
        dialog = GroupEditDialog(group_config)
        dialog.setWindowTitle("Add Group")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.group_added.emit(group_config)

    def _edit_group(self, group_id: str):
        group_config = self._config.groups.get(group_id)
        assert group_config is not None

        dialog = GroupEditDialog(group_config)
        dialog.setWindowTitle("Edit Group")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.group_edited.emit(group_config)

    def _list_pipelines(self):
        pipeline_types = list(self.plugin_api.pipeline_types.get_pipeline_types().values())
        pipeline_list_dialog = PipelineListDialog(self.controller, pipeline_types)
        pipeline_list_dialog.setWindowTitle("Pipelines")
        pipeline_list_dialog.exec()

    def _add_pipeline(self):
        pipeline_config = PipelineConfig()
        pipeline_types = list(self.plugin_api.pipeline_types.get_pipeline_types().values())
        dialog = PipelineConfigDialog(pipeline_types, pipeline_config, self)
        dialog.setWindowTitle("Add pipeline")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.pipeline_added.emit(pipeline_config)

    def _edit_pipeline(self):
        pipeline_config = self._config.pipeline
        pipeline_types = list(self.plugin_api.pipeline_types.get_pipeline_types().values())
        dialog = PipelineConfigDialog(pipeline_types, pipeline_config, self)
        dialog.setWindowTitle("Edit pipeline")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.pipeline_edited.emit(pipeline_config)

    def _config_changed(self, config):
        self._config = config

    def keyPressEvent(self, event):
        pass
