import time
from pathlib import Path
from typing import Protocol, Optional, Callable

import reactivex as rx
from py3r.media.types import VideoFrame
from py3r.media.video.ffmpeg_video_file_source import FFmpegVideoFileSource
from reactivex import operators as ops
from reactivex.disposable import Disposable
from reactivex.scheduler import EventLoopScheduler

from flow3r.core.streaming.abc.transform import Transform
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.core.typing.video_segment import VideoSegmentFormat, VideoSegment


class IVideoReader(Protocol):
    def open(self) -> None: ...
    def read(self) -> Optional["VideoFrame"]: ...  # returns None at EOF
    def close(self) -> None: ...


VideoReaderFactory = Callable[[Path, VideoFormat], IVideoReader]

def default_video_reader_factory(video_file: Path, desc: VideoFormat):
    return FFmpegVideoFileSource(video_file, grayscale=desc.fmt=="mono8")


class VideoSegmentReader(Transform[VideoSegmentFormat, VideoSegment, VideoFormat, VideoFrame]):
    def __init__(self, reader_factory: VideoReaderFactory = default_video_reader_factory):
        self._reader_factory = reader_factory
        # io_workers=1 keeps strict segment order even if someone changes operators later
        self._io_sched = EventLoopScheduler()

        self._video_format: Optional[VideoFormat] = None

    def infer_descriptor(self, desc_in: VideoSegmentFormat) -> VideoFormat:
        # Re-emitting the original format is usually what you want
        return desc_in.video_format  # adjust field name to yours

    def setup(self, desc_in: VideoSegmentFormat) -> None:
        self._video_format = desc_in.video_format

    def transform_observable(self, obs: rx.Observable[VideoSegment]) -> rx.Observable[VideoFrame]:
        def read_segment(seg: VideoSegment) -> rx.Observable[VideoFrame]:
            def factory(observer, _sched=None):
                closed = False
                reader = None

                def cleanup():
                    nonlocal closed, reader
                    if closed:
                        return
                    closed = True
                    if reader is not None:
                        try:
                            reader.close()
                        finally:
                            reader = None

                try:
                    reader = self._reader_factory(seg.file_path, self._video_format)
                    reader.open()
                except Exception as exc:
                    observer.on_error(exc)
                    cleanup()
                    return Disposable(cleanup)

                # Stream frames, restoring metadata
                try:
                    metas = seg.frame_metas
                    for meta in metas:
                        if closed:
                            break

                        frame = reader.read()
                        if frame is None:
                            # file ended early (corruption or mismatch)
                            observer.on_error(RuntimeError(
                                f"EOF before expected frame metas finished for {seg.file_path}"
                            ))
                            cleanup()
                            return Disposable(cleanup)

                        # IMPORTANT: overwrite/attach the meta so downstream sees “as if live”
                        # adapt to your VideoFrame structure
                        frame = frame.with_meta(meta)
                        observer.on_next(frame)

                        time.sleep(0.01)

                    # Optionally verify there are no extra frames beyond metas
                    # extra = reader.read()
                    # if extra is not None: warn or error

                    observer.on_completed()
                except Exception as exc:
                    observer.on_error(exc)
                finally:
                    cleanup()

                return Disposable(cleanup)

            return rx.create(factory).pipe(
                # run the blocking read loop off the caller thread
                ops.subscribe_on(self._io_sched)
            )

        # concat_map ensures: segment1 frames, then segment2 frames, in order
        return obs.pipe(ops.concat_map(read_segment))
