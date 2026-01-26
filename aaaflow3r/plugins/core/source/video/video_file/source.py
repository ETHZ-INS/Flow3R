from pathlib import Path

from py3r.media.types import VideoFrame
from py3r.media.video.ffmpeg_video_file_source import FFmpegVideoFileSource
from reactivex import operators as ops
from reactivex.subject import ReplaySubject

from aaaflow3r.core.source.abc.source import ISource
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.plugins.core.source.video.source_observable import source_observable
from aaaflow3r.plugins.core.source.video.video_file.config import VideoFileSourceConfig
from aaaflow3r.plugins.core.typing.video import VideoFormat


class VideoFileSource(ISource[VideoFrame]):
    def __init__(self, config: VideoFileSourceConfig):
        self._video_source = FFmpegVideoFileSource(Path(config.file_path), playback=True)
        self._desc_subject = ReplaySubject(1)
        self._frame_observable = source_observable(self._video_source)
        self._stream = Stream(self._desc_subject, self._frame_observable.pipe(ops.share()))

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
