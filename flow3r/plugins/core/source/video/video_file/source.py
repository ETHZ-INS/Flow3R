from pathlib import Path

from py3r.media.types import VideoFrame
from py3r.media.video.ffmpeg_video_file_source import FFmpegVideoFileSource
from reactivex import operators as ops

from flow3r.core.source.abc.source import ISource
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.source.video.source_observable import source_observable
from flow3r.plugins.core.source.video.video_file.config import VideoFileSourceConfig
from flow3r.plugins.core.typing.video import VideoFormat


class VideoFileSource(ISource[VideoFormat, VideoFrame]):
    def __init__(self, config: VideoFileSourceConfig):
        print(config.loop)
        self._video_source = FFmpegVideoFileSource(Path(config.file_path), grayscale=config.grayscale, playback=True, loop=config.loop)

        fmt = VideoFormat(
            self._video_source.get_size(),
            self._video_source.get_fps(),
            "mono8" if self._video_source.get_num_channels() == 1 else "rgb24"
        )

        self._frame_observable = source_observable(self._video_source)
        self._stream = Stream(fmt, self._frame_observable.pipe(ops.share()))

    @property
    def stream(self) -> Stream[VideoFormat, VideoFrame]:
        return self._stream

    def open(self):
        pass

    def close(self):
        pass
