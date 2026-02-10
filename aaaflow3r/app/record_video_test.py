import sys
import time

from PySide6.QtWidgets import QApplication
from reactivex import Subject, operators as ops
from reactivex.subject import ReplaySubject

from aaaflow3r.app.api.app.app_context import AppContext
from aaaflow3r.app.api.plugins.plugins import PluginAPI
from aaaflow3r.app.widgets.main_window import MainWindow
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.plugins.core.pipeline.record_video.pipeline import RecordVideoPipeline
from aaaflow3r.plugins.core.plugin import CorePlugin
from aaaflow3r.plugins.core.source.audio.microphone.config import MicrophoneSourceConfig
from aaaflow3r.plugins.core.source.audio.microphone.source import MicrophoneSource
from aaaflow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig
from aaaflow3r.plugins.core.source.video.webcam.source import WebcamSource
from aaaflow3r.plugins.test.pipeline.test.pipeline import TestPipeline
from aaaflow3r.plugins.test.source.test.source import VideoTestSource

plugins = [CorePlugin()]

api = PluginAPI()

for plugin in plugins:
    plugin.initialize(api)

app = QApplication(sys.argv)

window = MainWindow(api)
window.setWindowTitle("Flow3R")
window.show()

app_context = AppContext(window.widget_service)

start = ReplaySubject(1)
stop = ReplaySubject(1)

video_source = WebcamSource(WebcamSourceConfig(device_index=0))
video_source2 = VideoTestSource()
audio_source = MicrophoneSource(MicrophoneSourceConfig(device_index=0))

#pipeline = TestPipeline()
pipeline = RecordVideoPipeline()

video_stream = Stream(video_source.stream.descriptor, video_source.stream.observable.pipe(ops.take(300)))

sources = [video_stream]#, audio_source.stream, video_source2.stream]
pipeline_interface = pipeline.build(app_context, sources)

video_source.open()
audio_source.open()
video_source2.open()

#start.on_next(None)
#input("Press enter to stop...")
#stop.on_next(None)
#
sys.exit(app.exec())
