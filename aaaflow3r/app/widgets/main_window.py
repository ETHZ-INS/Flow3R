from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMainWindow, QDialog

from aaaflow3r.app.api.plugins.plugins import PluginAPI
from aaaflow3r.app.config.app_config import AppConfig
from aaaflow3r.app.layout.main_window import Ui_WelfareRecorder
from aaaflow3r.app.controller import Controller
from aaaflow3r.app.widget_service import WidgetService
from aaaflow3r.app.widgets.pipeline_config_dialog import PipelineConfigDialog
from aaaflow3r.app.widgets.source_config_dialog import SourceConfigDialog
from aaaflow3r.core.source.source_config import SourceConfig


class MainWindow(Ui_WelfareRecorder, QMainWindow):
    add_source = Signal(object)  # source config
    edit_source = Signal(object)  # source config

    edit_pipeline = Signal(object)

    stop_recording = Signal(str)

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

        self.plugin_api = plugin_api

        self.widget_service = WidgetService(self.dock_window, self.plugin_api.visualizer_types.get_visualizer_types())

        self.controller = Controller(self.plugin_api.source_types.get_source_types(), self.plugin_api.pipeline_types.get_pipeline_types(), self.widget_service)
        self.widget_service.controller = self.controller

        self.worker_thread = QThread()
        self.controller.moveToThread(self.worker_thread)
        self.worker_thread.setObjectName("SourceControllerThread")
        self.worker_thread.start()

        self.action_add_camera.triggered.connect(self._add_source)

        self.add_source.connect(self.controller.add_source)
        self.edit_source.connect(self.controller.edit_source)

        self.edit_pipeline.connect(self.controller.edit_pipeline)
        self.stop_recording.connect(self.controller.stop_recording)

        self.controller.config_changed.connect(self._config_changed)

        self._config: AppConfig = None

    def _add_source(self):
        source_config = SourceConfig()
        dialog = SourceConfigDialog(list(self.plugin_api.source_types.get_source_types().values()), source_config, self)
        dialog.setWindowTitle("Add source")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            print(source_config)
            self.add_source.emit(source_config)

    def _edit_source(self, source_id: str):
        source_config = self._config.sources.get(source_id)
        assert source_config is not None

        source_types = list(self.plugin_api.source_types.get_source_types().values())
        dialog = SourceConfigDialog(source_types, source_config, self)
        dialog.setWindowTitle("Edit source")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.edit_source.emit(source_config)

    def _edit_pipeline(self):
        pipeline_config = self._config.pipeline
        pipeline_types = list(self.plugin_api.pipeline_types.get_pipeline_types().values())
        dialog = PipelineConfigDialog(pipeline_types, pipeline_config, self)
        dialog.setWindowTitle("Edit pipeline")
        res = dialog.exec()

        if res == QDialog.DialogCode.Accepted:
            self.edit_pipeline.emit(pipeline_config)

    def _config_changed(self, config):
        print(config)
        self._config = config

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Delete:
            self.controller.remove_source(list(self._config.sources.values())[0].id)
        elif event.key() == QtCore.Qt.Key.Key_E:
            self._edit_source(list(self._config.sources.values())[0].id)
        elif event.key() == QtCore.Qt.Key.Key_O:
            self._edit_pipeline()
        elif event.key() == QtCore.Qt.Key.Key_S:
            self.stop_recording.emit(list(self._config.sources.values())[0].id)
