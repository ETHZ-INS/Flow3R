import tempfile
from pathlib import Path
from typing import Callable, Protocol, Optional, List

import reactivex as rx
from py3r.media.types import VideoFrame, FrameMeta
from py3r.media.video.ffmpeg_video_file_writer import FFmpegVideoFileWriter
from reactivex.disposable import Disposable

from flow3r.core.streaming.abc.transform import Transform
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.core.typing.video_segment import VideoSegmentFormat, VideoSegment


class IVideoWriter(Protocol):
    def open(self): ...
    def write(self, frame: VideoFrame): ...
    def close(self): ...


SegmentFileFactory = Callable[[int], Path]
VideoWriterFactory = Callable[[Path, VideoFormat], IVideoWriter]


def default_segment_file_factory(folder: Path):
    def _factory(segment_index: int):
        return folder / f"segment_{segment_index}.mp4"
    return _factory


def default_video_writer_factory(segment_file: Path, desc: VideoFormat):
    segment_file.parent.mkdir(parents=True, exist_ok=True)
    return FFmpegVideoFileWriter(segment_file, desc.size, desc.fps, grayscale=desc.fmt=="mono8", quality="high")


class VideoSegmentWriter(Transform[VideoFormat, VideoFrame, VideoSegmentFormat, VideoSegment]):
    def __init__(
        self,
        *,
        segment_file_factory: Optional[SegmentFileFactory] = None,
        folder: Optional[Path] = None,
        writer_factory: VideoWriterFactory = default_video_writer_factory,
        segment_length_seconds: float = 5.0
    ):
        if segment_file_factory is not None and folder is not None:
            raise ValueError("Pass either segment_file_factory or folder, not both.")

        if segment_file_factory is not None:
            self._segment_file_factory = segment_file_factory
        else:
            folder = folder or Path(tempfile.mkdtemp(prefix="video_segments_"))
            self._segment_file_factory = default_segment_file_factory(folder)

        self._writer_factory = writer_factory
        self._segment_length_seconds = segment_length_seconds

        self._video_format: VideoFormat = None
        self._segment_length_frames: int = None
        self._segment_index: int = None
        self._segment_file: Path = None
        self._writer: Optional[IVideoWriter] = None
        self._frame_metas: List[FrameMeta] = []

    def setup(self, desc_in: VideoFormat) -> None:
        self._segment_length_frames = int(desc_in.fps * self._segment_length_seconds)
        self._segment_index = 0
        self._video_format = desc_in

    def infer_format(self, desc_in: VideoFormat) -> VideoSegmentFormat:
        return VideoSegmentFormat(desc_in, self._segment_length_seconds)

    def transform_observable(self, obs: rx.Observable[VideoFrame]) -> rx.Observable[VideoSegment]:
        # This is naturally stateful, so rx.create is appropriate.
        def factory(observer, _sched=None):
            closed = False
            sub = None

            def open_segment():
                self._segment_file = self._segment_file_factory(self._segment_index)
                self._writer = self._writer_factory(self._segment_file, self._video_format)
                self._writer.open()

            def close_segment():
                if self._writer is None:
                    return
                try:
                    self._writer.close()
                finally:
                    self._writer = None

                observer.on_next(VideoSegment(
                    segment_index=self._segment_index,
                    file_path=self._segment_file,
                    frame_metas=self._frame_metas
                ))
                self._segment_index += 1
                self._segment_file = None
                self._frame_metas = []

            def cleanup_inner():
                nonlocal closed, sub
                if closed:
                    return
                closed = True
                if sub is not None:
                    sub.dispose()
                # ensure any open writer is closed (do not emit segment here unless you want)
                if self._writer is not None:
                    try:
                        self._writer.close()
                    finally:
                        self._writer = None

            def on_next(fr: VideoFrame):
                if self._writer is None:
                    open_segment()

                # rotate
                if len(self._frame_metas) >= self._segment_length_frames:
                    close_segment()
                    open_segment()

                # write frame
                self._frame_metas.append(FrameMeta.from_meta(fr))
                self._writer.write(fr)

            def on_error(e: Exception):
                try:
                    if self._writer is not None and len(self._frame_metas) > 0:
                        close_segment()
                    observer.on_error(e)
                finally:
                    cleanup_inner()

            def on_completed():
                try:
                    if self._writer is not None and len(self._frame_metas) > 0:
                        close_segment()
                    observer.on_completed()
                finally:
                    cleanup_inner()

            sub = obs.subscribe(on_next, on_error, on_completed)
            return Disposable(cleanup_inner)

        return rx.create(factory)

    def cleanup(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None
