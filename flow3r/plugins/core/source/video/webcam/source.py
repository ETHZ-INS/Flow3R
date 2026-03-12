import cv2
from py3r.media.types import VideoFrame
from py3r.media.video.opencv_webcam_source import OpenCVWebcamSource

from reactivex import operators as ops
from reactivex.subject import ReplaySubject

from flow3r.core.source.abc.source import ISource
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.source.video.source_observable import source_observable
from flow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig
from flow3r.plugins.core.typing.video import VideoFormat


class WebcamSource(ISource[VideoFormat, VideoFrame]):
    def __init__(self, config: WebcamSourceConfig):
        self._video_source = OpenCVWebcamSource(config.device_index, grayscale=config.grayscale)
        fmt = VideoFormat(
            self._video_source.get_size(),
            self._video_source.get_fps(),
            "mono8" if self._video_source.get_num_channels() == 1 else "rgb24"
        )
        data = source_observable(self._video_source).pipe(ops.map(lambda f: f.with_image(cv2.cvtColor(f.img, cv2.COLOR_BGR2RGB))), ops.share())
        self._stream = Stream(fmt, data)

    @property
    def stream(self) -> Stream[VideoFormat, VideoFrame]:
        return self._stream

    def open(self):
        pass

    def close(self):
        pass
