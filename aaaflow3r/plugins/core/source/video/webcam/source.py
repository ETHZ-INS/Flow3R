import random

from py3r.media.types import VideoFrame
from py3r.media.video.opencv_webcam_source import OpenCVWebcamSource

from reactivex import Subject, operators as ops
from reactivex.subject import ReplaySubject

from aaaflow3r.core.source.abc.source import ISource
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.plugins.core.source.video.source_observable import source_observable
from aaaflow3r.plugins.core.source.video.webcam.config import WebcamSourceConfig
from aaaflow3r.plugins.core.typing.video import VideoFormat


class WebcamSource(ISource[VideoFrame]):
    def __init__(self, config: WebcamSourceConfig):
        if random.random() < 0.5:
            raise Exception("Oh no!")
        self._video_source = OpenCVWebcamSource(config.device_index)
        self._desc_subject = ReplaySubject(1)
        self._frame_observable = source_observable(self._video_source).pipe(ops.share())
        self._stream = Stream(self._desc_subject, self._frame_observable)

    @property
    def stream(self) -> Stream[VideoFrame]:
        return self._stream

    def open(self):
        size = self._video_source.get_size()
        fps = self._video_source.get_fps()
        fmt = "mono8" if self._video_source.get_num_channels() == 1 else "rgb24"
        self._desc_subject.on_next(VideoFormat(size, fps, fmt))

    def close(self):
        self._desc_subject.on_completed()
