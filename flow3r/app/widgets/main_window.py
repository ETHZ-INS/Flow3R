import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

from PySide6.QtCore import QThread, Signal, Slot, QTimer
from PySide6.QtGui import QColor, Qt, QTextCursor, QTextCharFormat
from PySide6.QtWidgets import QMainWindow, QDialog, QWidget, QVBoxLayout, QFileDialog, QMessageBox

from flow3r.app.api.app.app_context import AppContext
from flow3r.app.api.app.settings_service import SettingsService
from flow3r.app.api.plugins.plugins import PluginAPI
from flow3r.app.config.app_config import AppConfig
from flow3r.app.config.group_config import GroupConfig
from flow3r.app.config.placeholder_config import PlaceholderConfig
from flow3r.app.layout.main_window import Ui_WelfareRecorder
from flow3r.app.controller.controller import Controller
from flow3r.app.api.app.navigator_service import NavigatorService
from flow3r.app.controller.widget_controller import WidgetController
from flow3r.app.api.app.widget_service import WidgetService
from flow3r.app.widgets.global_placeholder_dialog import GlobalPlaceholderDialog
from flow3r.app.widgets.group_edit_dialog import GroupEditDialog
from flow3r.app.widgets.group_list_dialog import GroupListDialog
from flow3r.app.widgets.pipeline_config_dialog import PipelineConfigDialog
from flow3r.app.widgets.pipeline_list_dialog import PipelineListDialog
from flow3r.app.widgets.placeholder_edit_dialog import PlaceholderEditDialog
from flow3r.app.widgets.placeholder_list_dialog import PlaceholderListDialog
from flow3r.app.widgets.source_config_dialog import SourceConfigDialog
from flow3r.app.widgets.source_list_dialog import SourceListDialog
from flow3r.app.config.pipeline_config import PipelineConfig
from flow3r.app.config.source_config import SourceConfig


LOG_COLORS = {
    "INFO": QColor("black"),
    "WARNING": QColor("orange"),
    "ERROR": QColor("red"),
}


LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
AUTO_SAVE_FILE = LOCALAPPDATA / "ETH3RHub" / "Flow3R" / "auto_save.f3r"


class MainWindow(Ui_WelfareRecorder, QMainWindow):
    config_loaded = Signal(str)
    config_saved = Signal(str, object, bool)

    settings_changed = Signal(object)  # settings object

    source_added = Signal(object)  # source config
    source_edited = Signal(object)  # source config

    group_added = Signal(object)  # group config
    group_edited = Signal(object)  # group config

    pipeline_added = Signal(object)  # pipeline config
    pipeline_edited = Signal(object)  # pipeline config

    placeholder_added = Signal(object)  # placeholder config
    placeholder_edited = Signal(object)  # placeholder config

    group_assigned_to_source = Signal(str, object)  # source_id, group_id
    pipeline_assignment_changed = Signal(str, object, object)  # group_id, pipeline_ids, source_mapping

    def __init__(self, plugin_api: PluginAPI, config_file: Path = None, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setupUi(self)
        self.setStyleSheet("QPushButton:disabled {color: gray}")

        inner = QWidget()
        vbox = QVBoxLayout(inner)
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
        self._build_settings_menus()

        self.config_file: Optional[Path] = config_file
        self.super_user: bool = False
        self.auto_save: bool = True

        settings_menus = {menu.path: menu for menu in self.plugin_api.settings_menus.get_settings_menus().values()}
        self.navigator_service = NavigatorService(settings_menus, default_parent=self)

        self.widget_controller = WidgetController(self.dock_window, self.frm_recordings, list(self.plugin_api.visualizer_types.get_visualizer_types().values()))
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

        self.controller = Controller(self.plugin_api, self.widget_service)
        self.widget_controller._main_window = self
        self.widget_controller.set_controller(self.controller)

        self.settings_service = SettingsService(self.controller)

        self.app_context = AppContext(self.navigator_service, self.settings_service)
        self.navigator_service.set_app_context(self.app_context)

        self.worker_thread = QThread()
        self.controller.moveToThread(self.worker_thread)
        self.worker_thread.setObjectName("SourceControllerThread")
        self.worker_thread.start()

        self.action_superuser_mode.setCheckable(True)
        self.action_superuser_mode.triggered.connect(self.toggle_super_user)

        self.action_save_project.triggered.connect(self.save_project)
        self.action_load_project.triggered.connect(self.load_project)
        self.action_save_project_as.triggered.connect(self.save_project_as)

        self.action_list_sources.triggered.connect(self._list_sources)
        self.action_list_groups.triggered.connect(self._list_groups)
        self.action_list_pipelines.triggered.connect(self._list_pipelines)
        self.action_list_placeholders.triggered.connect(self._list_placeholders)

        self.action_add_source.triggered.connect(self._add_source)
        self.action_add_group.triggered.connect(self._add_group)
        self.action_add_pipeline.triggered.connect(self._add_pipeline)
        self.action_add_placeholder.triggered.connect(self._add_placeholder)
        self.action_set_placeholder_values.triggered.connect(self._set_global_placeholders)

        self.config_saved.connect(self.controller.save_config)
        self.config_loaded.connect(self.controller.load_config)

        self.settings_changed.connect(self.controller.set_settings)

        self.source_added.connect(self.controller.add_source)
        self.source_edited.connect(self.controller.edit_source)

        self.group_added.connect(self.controller.add_group)
        self.group_edited.connect(self.controller.edit_group)

        self.pipeline_added.connect(self.controller.add_pipeline)
        self.pipeline_edited.connect(self.controller.edit_pipeline)

        self.placeholder_added.connect(self.controller.add_placeholder)
        self.placeholder_edited.connect(self.controller.edit_placeholder)

        self.group_assigned_to_source.connect(self.controller.assign_group)
        self.pipeline_assignment_changed.connect(self.controller.set_pipeline_assignment)

        self.controller.log_message.connect(self.add_log_entry)
        self.controller.config_changed.connect(self._config_changed)
        self.controller.error.connect(self._on_error)
        self.controller.config_loaded.connect(self._project_loaded)

        self._config: AppConfig = deepcopy(self.controller.config)

        self.add_log_entry("Application started", "INFO")

        if self.config_file is not None:
            QTimer.singleShot(0, lambda: self.load_project())
        elif AUTO_SAVE_FILE.exists():
            QTimer.singleShot(0, lambda: self.ask_load_auto_save())

    def _build_settings_menus(self):
        top_level_menu = self.menuBar().addMenu("Settings")

        menus = {}
        def _get_menu(path: Tuple[str, ...]):
            if path in menus:
                return menus[path]
            else:
                if len(path) == 0:
                    return top_level_menu
                return _get_menu(path[:-1]).addMenu(path[-1])

        for settings_menu in self.plugin_api.settings_menus.get_settings_menus().values():
            parent_menu = _get_menu(settings_menu.path[:-1])
            action = parent_menu.addAction(settings_menu.path[-1])
            action.triggered.connect(lambda _, path=settings_menu.path: self._open_settings_menu(path))

    @Slot()
    def toggle_super_user(self):
        self.super_user = not self.super_user
        self.action_superuser_mode.setChecked(self.super_user)
        self.setWindowTitle("Flow3R" if not self.super_user else "Flow3R (Super User)")

    @Slot(str, str)
    def add_log_entry(self, message: str, level: str = "INFO"):
        edit = self.txt_log
        sb = edit.verticalScrollBar()
        stick = (sb.value() == sb.maximum())

        cursor = edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

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

    def _open_settings_menu(self, path: Tuple[str, ...]):
        self.navigator_service.open(path, parent=self)

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
        source_config = deepcopy(self._config.sources.get(source_id))
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
        group_config = deepcopy(self._config.all_groups.get(group_id))
        assert group_config is not None

        dialog = GroupEditDialog(group_config)
        dialog.setWindowTitle("Edit Group")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.group_edited.emit(group_config)

    def _list_pipelines(self):
        pipeline_types = list(self.plugin_api.pipeline_types.get_pipeline_types().values())
        pipeline_list_dialog = PipelineListDialog(self.app_context, self.controller, pipeline_types)
        pipeline_list_dialog.setWindowTitle("Pipelines")
        pipeline_list_dialog.exec()

    def _add_pipeline(self):
        pipeline_config = PipelineConfig()
        pipeline_types = list(self.plugin_api.pipeline_types.get_pipeline_types().values())
        dialog = PipelineConfigDialog(self.app_context, pipeline_types, pipeline_config, self)
        dialog.setWindowTitle("Add Pipeline")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.pipeline_added.emit(pipeline_config)

    def _list_placeholders(self):
        placeholder_list_dialog = PlaceholderListDialog(self.controller)
        placeholder_list_dialog.setWindowTitle("Placeholders")
        placeholder_list_dialog.exec()

    def _add_placeholder(self):
        placeholder_config = PlaceholderConfig()
        dialog = PlaceholderEditDialog(placeholder_config, self)
        dialog.setWindowTitle("Add Placeholder")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.placeholder_added.emit(placeholder_config)

    def _set_global_placeholders(self):
        dialog = GlobalPlaceholderDialog(self.controller)
        dialog.setWindowTitle("Global Placeholders")
        res = dialog.exec()

    def _config_changed(self, config):
        self._config = config

        if self.auto_save:
            self._save_project(AUTO_SAVE_FILE)

    def _select_save_file(self):
        if self.config_file is None:
            # Default path when opening the file dialog
            selected_file = str(Path.home() / "project.f3r")
        else:
            selected_file = str(self.config_file)

        file_filter = "Flow3R Config Files (*.f3r)"
        selected_file, _ = QFileDialog.getSaveFileName(self, "Save Project", selected_file, file_filter)

        return Path(selected_file) if selected_file else None

    def _select_load_file(self):
        if self.config_file is None:
            # Default path when opening the file dialog
            directory = str(Path.home())
        else:
            directory = str(self.config_file)

        selected_filter = "Flow3R Config Files (*.f3r)"
        file_filter = "All files (*.*);;Flow3R Config Files (*.f3r)"
        selected_file, _ = QFileDialog.getOpenFileName(self, "Load Project", directory, file_filter, selected_filter)

        return Path(selected_file) if selected_file else None

    def save_project(self):
        if self.config_file is None:
            self.save_project_as()
            return
        self._save_project(self.config_file)
        AUTO_SAVE_FILE.unlink(missing_ok=True)

    def save_project_as(self):
        selected_file = self._select_save_file()
        if not selected_file:
            return
        self.config_file = Path(selected_file)
        self._save_project(self.config_file)
        AUTO_SAVE_FILE.unlink(missing_ok=True)

    def _save_project(self, config_file: Path):
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

        self.config_saved.emit(str(config_file), ui_state, self.super_user)

    def load_project(self):
        selected_file = self._select_load_file()
        if not selected_file:
            return

        self.config_file = Path(selected_file)
        self._load_project(self.config_file)

    def ask_load_auto_save(self):
        popup = QMessageBox(self)
        popup.setWindowTitle("Recover Auto-Save")
        popup.setText("Do you want to load the last auto-saved project?")
        popup.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        popup.setDefaultButton(QMessageBox.StandardButton.Yes)
        res = popup.exec()
        if res == QMessageBox.StandardButton.Yes:
            self._load_project(AUTO_SAVE_FILE)

    def _load_project(self, config_file: Path):
        self.config_loaded.emit(str(config_file))

    def _project_loaded(self, ui_state: dict):
        geometry = ui_state.get("geometry")
        window_state = ui_state.get("window_state")
        dock_window_geometry = ui_state.get("dock_window_geometry")
        dock_window_state = ui_state.get("dock_window_state")

        #if geometry:
        #    self.restoreGeometry(geometry)
        if window_state:
            self.restoreState(window_state)
        if dock_window_geometry:
            self.dock_window.restoreGeometry(dock_window_geometry)
        if dock_window_state:
            self.dock_window.restoreState(dock_window_state)

        if any(
            self._config.global_placeholder_values.get(placeholder_config.id) is None
            for placeholder_config in self._config.placeholders.values()
            if placeholder_config.is_global and not placeholder_config.is_constant
        ):
            self._set_global_placeholders()

    def _on_error(self, message: str, exc: Optional[Exception] = None):
        error_message = message
        if exc:
            error_message += f": {exc}"

        self.add_log_entry(error_message, "ERROR")

        popup = QMessageBox(self)
        popup.setWindowTitle("Error")
        popup.setText(error_message)
        popup.setStandardButtons(QMessageBox.StandardButton.Ok)
        popup.exec()

    def keyPressEvent(self, event):
        pass

    def closeEvent(self, event):
        self.worker_thread.quit()
        self.worker_thread.wait(5000)  # 5-second grace period
        super().closeEvent(event)
