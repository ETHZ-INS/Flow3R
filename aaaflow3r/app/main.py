import os
import sys

from PySide6.QtWidgets import QApplication

from aaaflow3r.app.api.plugins.plugins import PluginAPI
from aaaflow3r.app.widgets.main_window import MainWindow
from aaaflow3r.plugins.core.plugin import CorePlugin
from aaaflow3r.plugins.pose_estimation.plugin import PoseEstimationPlugin

if __name__ == "__main__":
    os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
    os.environ['OPENCV_FFMPEG_LOGLEVEL'] = "-8"

    app = QApplication(sys.argv)

    api = PluginAPI()
    core_plugin = CorePlugin()
    core_plugin.initialize(api)

    pose_estimation_plugin = PoseEstimationPlugin()
    pose_estimation_plugin.initialize(api)

    window = MainWindow(api)
    window.setWindowTitle("Flow3R")
    window.show()

    sys.exit(app.exec())
