import random

from py3r.media.types import VideoFrame
from py3r.media.video.opencv_webcam_source import OpenCVWebcamSource

from reactivex import Subject, operators as ops
from reactivex.subject import ReplaySubject

from flow3r.core.source.abc.source import ISource
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.source.video.source_observable import source_observable
from flow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig
from flow3r.plugins.core.typing.video import VideoFormat


class WebcamSource(ISource[VideoFormat, VideoFrame]):
    def __init__(self, config: WebcamSourceConfig):
        self._video_source = OpenCVWebcamSource(config.device_index)
        self._desc_subject = ReplaySubject(1)
        self._frame_observable = source_observable(self._video_source).pipe(ops.share())
        self._stream = Stream(self._desc_subject, self._frame_observable)

    @property
    def stream(self) -> Stream[VideoFormat, VideoFrame]:
        return self._stream

    def open(self):
        size = self._video_source.get_size()
        fps = self._video_source.get_fps()
        fmt = "mono8" if self._video_source.get_num_channels() == 1 else "rgb24"
        self._desc_subject.on_next(VideoFormat(size, fps, fmt))

    def close(self):
        self._desc_subject.on_completed()
