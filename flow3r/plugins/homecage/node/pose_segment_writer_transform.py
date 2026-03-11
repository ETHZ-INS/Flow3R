import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Callable, Protocol, Optional, Tuple

import reactivex as rx
from py3r.pose.core.serialization.dynamic_csv_writer import DynamicPoseCSVWriter
from py3r.pose.core.types import VideoFramePoses
from reactivex.disposable import Disposable

from flow3r.core.streaming.abc.transform import Transform
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.homecage.typing.pose_segment import PoseSegmentFormat, PoseSegment
from flow3r.plugins.pose_estimation.typing.pose_format import PoseFormat


class IPoseWriter(Protocol):
    def open(self): ...
    def write(self, poses: VideoFramePoses): ...
    def close(self): ...


SegmentFileFactory = Callable[[int], Path]
PoseWriterFactory = Callable[[Path, PoseFormat], IPoseWriter]


def default_segment_file_factory(folder: Path):
    def _factory(segment_index: int):
        return folder / f"segment_{segment_index}.csv"
    return _factory


def default_pose_writer_factory(segment_file: Path, desc: PoseFormat):
    segment_file.parent.mkdir(parents=True, exist_ok=True)
    return DynamicPoseCSVWriter(segment_file)


class PoseSegmentWriter(Transform[Tuple[VideoFormat, PoseFormat], VideoFramePoses, PoseSegmentFormat, PoseSegment]):
    def __init__(
        self,
        *,
        segment_file_factory: Optional[SegmentFileFactory] = None,
        folder: Optional[Path] = None,
        writer_factory: PoseWriterFactory = default_pose_writer_factory,
        segment_length_seconds: float = 5.0
    ):
        if segment_file_factory is not None and folder is not None:
            raise ValueError("Pass either segment_file_factory or folder, not both.")

        if segment_file_factory is not None:
            self._segment_file_factory = segment_file_factory
        else:
            folder = folder or Path(tempfile.mkdtemp(prefix="pose_segments_"))
            self._segment_file_factory = default_segment_file_factory(folder)

        self._writer_factory = writer_factory
        self._segment_length_seconds = segment_length_seconds

        self._pose_format: PoseFormat = None
        self._segment_length_frames: int = None
        self._segment_index: int = None
        self._segment_file: Path = None
        self._writer: Optional[IPoseWriter] = None
        self._num_frames: int = 0

    def setup(self, desc_in: Tuple[VideoFormat, PoseFormat]) -> None:
        video_format, pose_format = desc_in
        self._segment_length_frames = int(video_format.fps * self._segment_length_seconds)
        self._segment_index = 0
        self._pose_format = pose_format

    def infer_format(self, desc_in: Tuple[VideoFormat, PoseFormat]) -> PoseSegmentFormat:
        return PoseSegmentFormat(desc_in[0], desc_in[1], self._segment_length_seconds)

    def transform_observable(self, obs: rx.Observable[VideoFramePoses]) -> rx.Observable[PoseSegment]:
        # This is naturally stateful, so rx.create is appropriate.
        def factory(observer, _sched=None):
            closed = False
            sub = None

            def open_segment():
                self._segment_file = self._segment_file_factory(self._segment_index)
                self._writer = self._writer_factory(self._segment_file, self._pose_format)
                self._writer.open()

            def close_segment():
                if self._writer is None:
                    return
                try:
                    self._writer.close()
                finally:
                    self._writer = None

                observer.on_next(PoseSegment(
                    segment_index=self._segment_index,
                    file_path=self._segment_file,
                ))
                self._segment_index += 1
                self._num_frames = 0
                self._segment_file = None

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

            def on_next(poses: VideoFramePoses):
                if self._writer is None:
                    open_segment()

                # rotate
                if self._num_frames >= self._segment_length_frames:
                    close_segment()
                    open_segment()

                poses = replace(poses, frame_index=self._num_frames)
                # write frame
                self._writer.write(poses)
                self._num_frames += 1

            def on_error(e: Exception):
                try:
                    if self._writer is not None and self._num_frames > 0:
                        close_segment()
                    observer.on_error(e)
                finally:
                    cleanup_inner()

            def on_completed():
                try:
                    if self._writer is not None and self._num_frames > 0:
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
