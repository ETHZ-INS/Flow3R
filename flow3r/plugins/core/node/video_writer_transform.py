from pathlib import Path
from typing import Callable, Optional, Protocol

from py3r.media.types import VideoFrame
from py3r.media.video.ffmpeg_video_file_writer import FFmpegVideoFileWriter

from flow3r.core.streaming.abc.finalize_transform import FinalizeTransform
from flow3r.plugins.core.typing.video import VideoFormat


class IVideoWriter(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, frame: VideoFrame) -> None: ...


VideoWriterFactory = Callable[[Path, VideoFormat], IVideoWriter]


def default_video_writer_factory(video_file: Path, desc: VideoFormat):
    return FFmpegVideoFileWriter(video_file, desc.size, desc.fps, grayscale=desc.fmt == "mono8", quality="high")


class VideoWriterTransform(FinalizeTransform[VideoFormat, VideoFrame, Path, Path]):
    """
    Writes video frames to a file and emits the file path at the end.
    """
    def __init__(self, video_file: Path, factory: VideoWriterFactory = default_video_writer_factory):
        super().__init__()
        self._video_file = video_file
        self._writer_factory = factory
        self._writer: Optional[IVideoWriter] = None

    def infer_descriptor(self, desc_in: VideoFormat) -> Path:
        # output descriptor can be the file path
        return self._video_file

    def setup(self, desc_in: VideoFormat) -> None:
        self._writer = self._writer_factory(self._video_file, desc_in)
        self._writer.open()

    def begin(self, desc_in: VideoFormat) -> None:
        # optional; not needed
        return None

    def on_item(self, item: VideoFrame) -> None:
        assert self._writer is not None
        self._writer.write(item)

    def finalize(self) -> Path:
        if self._writer is not None:
            try:
                self._writer.close()
            finally:
                self._writer = None
        return self._video_file
