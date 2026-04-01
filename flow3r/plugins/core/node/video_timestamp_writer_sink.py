from pathlib import Path
from typing import Callable, Optional, Protocol, Any

from py3r.media.types import VideoFrame

from flow3r.core.streaming.abc.sink import Sink
from flow3r.plugins.core.pipeline.util.timestamp_writer import TimestampWriter
from flow3r.plugins.core.typing.video import VideoFormat


class ITimestampWriter(Protocol):
    def open(self) -> None: ...
    def close(self) -> None: ...
    def write(self, timestamp: float) -> None: ...


TimestampWriterFactory = Callable[[Path, VideoFormat], ITimestampWriter]


def default_timestamp_writer_factory(file_path: Path, desc: VideoFormat):
    return TimestampWriter(file_path)


class VideoTimestampWriterSink(Sink[VideoFormat, VideoFrame]):
    def __init__(self, file_path: Path, factory: TimestampWriterFactory = default_timestamp_writer_factory):
        super().__init__()
        self._file_path = file_path
        self._factory = factory
        self._writer: Optional[ITimestampWriter] = None

    def setup(self, fmt: VideoFormat) -> None:
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._writer = self._factory(self._file_path, fmt)
            self._writer.open()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def on_next(self, item: VideoFrame) -> None:
        assert self._writer is not None
        self._writer.write(item.timestamp)

    def cleanup(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None
