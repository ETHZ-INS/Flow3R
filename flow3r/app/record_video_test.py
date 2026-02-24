import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from flow3r.app.api.plugins.plugins import PluginAPI
from flow3r.app.config.group_config import GroupConfig
from flow3r.app.widgets.main_window import MainWindow
from flow3r.core.pipeline.pipeline_config import PipelineConfig
from flow3r.core.source.source_config import SourceConfig
from flow3r.plugins.core.pipeline.record_video.config import RecordVideoConfig
from flow3r.plugins.core.plugin import CorePlugin
from flow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig
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

    window = MainWindow(api)
    window.setWindowTitle("Flow3R")
    window.show()

    source = SourceConfig()
    source.set_sub_config("Webcam", WebcamSourceConfig(device_index=0))

    group = GroupConfig()

    pipeline = PipelineConfig()
    pipeline.set_sub_config("Record Video", RecordVideoConfig("recordings/recording_{recording_number}.mp4"))

    window.pipeline_added.emit(pipeline)
    window.group_added.emit(group)
    window.source_added.emit(source)
    window.group_assigned_to_source.emit(source.id, group.id)
    window.pipeline_assigned_to_group.emit(group.id, pipeline.id)

    sys.exit(app.exec())
