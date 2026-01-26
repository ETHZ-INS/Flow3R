import time
from pathlib import Path
from typing import Optional

import numpy as np
from py3r.media.types import VideoFrame
from py3r.media.video.ffmpeg_video_file_source import FFmpegVideoFileSource

import reactivex as rx
from reactivex import Subject, Observable
from reactivex.abc import SchedulerBase
from reactivex.scheduler import CurrentThreadScheduler, EventLoopScheduler
from reactivex import operators as ops

from aaaflow3r.core.source.abc.source import ISource
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.plugins.core.typing.video import VideoFormat


def random_video_observable(
    width: int,
    height: int,
    fps: float,
    scheduler: Optional[SchedulerBase] = None,
) -> Observable[VideoFrame]:
    frame_interval_s = 1.0 / fps
    scheduler = scheduler or CurrentThreadScheduler.singleton()

    def _emit(observer, _scheduler):
        frame_index = 0
        t_ns = time.perf_counter_ns()

        try:
            while True:
                if frame_index == 10:
                    raise Exception("Test exception")

                img = np.random.randint(
                    0, 256, (height, width, 3), dtype=np.uint8
                )
                observer.on_next(VideoFrame(img, frame_index, t_ns))

                time.sleep(frame_interval_s)
                t_ns += int(frame_interval_s * 1e9)
                frame_index += 1
        except Exception as e:
            observer.on_error(e)

    return rx.create(_emit).pipe(
        # ensure generation runs off the subscriber thread
        ops.subscribe_on(scheduler)
    )


class VideoTestSource(ISource[VideoFrame]):
    def __init__(self):
        self._desc_subject = Subject()
        self._frame_observable = random_video_observable(64, 64, 1.0, EventLoopScheduler()).pipe(ops.share())
        self._stream = Stream(self._desc_subject, self._frame_observable)

    @property
    def stream(self) -> Stream[VideoFrame]:
        return self._stream

    def open(self):
        self._desc_subject.on_next(VideoFormat((64, 64), 1.0, "rgb24"))

    def close(self):
        self._desc_subject.on_completed()
