from pathlib import Path
from typing import Callable, Optional, Protocol

from py3r.media.types import VideoFrame
from py3r.media.video.ffmpeg_video_file_writer import FFmpegVideoFileWriter

from aaaflow3r.core.streaming.abc.sink import Sink
from aaaflow3r.plugins.core.typing.video import VideoFormat


class IVideoWriter(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, frame: VideoFrame) -> None: ...


VideoWriterFactory = Callable[[Path, VideoFormat], IVideoWriter]


def default_video_writer_factory(video_file: Path, desc: VideoFormat):
    return FFmpegVideoFileWriter(video_file, desc.size, desc.fps, grayscale=desc.fmt == "mono8", quality="high")


class VideoWriterSink(Sink[VideoFormat, VideoFrame]):
    def __init__(self, video_file: Path, factory: VideoWriterFactory = default_video_writer_factory):
        super().__init__()
        self._video_file = video_file
        self._factory = factory
        self._writer: Optional[IVideoWriter] = None

    def setup(self, desc: VideoFormat) -> None:
        try:
            print("VideoWriterSink setup:", self._video_file, desc)
            self._writer = self._factory(self._video_file, desc)
            self._writer.open()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def on_next(self, item: VideoFrame) -> None:
        assert self._writer is not None
        self._writer.write(item)

    def cleanup(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None
