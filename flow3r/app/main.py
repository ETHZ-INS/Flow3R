import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from flow3r.app.api.plugins.plugins import PluginAPI
from flow3r.app.widgets.main_window import MainWindow
from flow3r.plugins.core.plugin import CorePlugin
from flow3r.plugins.grimace.plugin import GrimacePlugin
from flow3r.plugins.pose_estimation.plugin import PoseEstimationPlugin

if __name__ == "__main__":
    os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
    os.environ['OPENCV_FFMPEG_LOGLEVEL'] = "-8"

    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("res/flow3r.png"))

    api = PluginAPI()
    core_plugin = CorePlugin()
    core_plugin.initialize(api)

    pose_estimation_plugin = PoseEstimationPlugin()
    pose_estimation_plugin.initialize(api)

    grimace_plugin = GrimacePlugin()
    grimace_plugin.initialize(api)

    window = MainWindow(api)
    window.setWindowTitle("Flow3R")
    window.show()

    sys.exit(app.exec())
