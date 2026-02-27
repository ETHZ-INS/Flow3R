from typing import Tuple

import reactivex as rx

from py3r.media.types import VideoFrame

from flow3r.core.streaming.abc.transform import Transform
from flow3r.plugins.core.typing.video import VideoFormat


class VideoSynchronizationTransform(Transform[VideoFormat, Tuple[VideoFrame, VideoFrame], VideoFormat, Tuple[VideoFrame, VideoFrame]]):
    def __init__(self):
        pass

    def setup(self, desc_in: VideoFormat) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def infer_descriptor(self, desc_in: VideoFormat) -> VideoFormat:
        return desc_in

    def transform_observable(self, obs: rx.Observable[Tuple[VideoFrame, VideoFrame]]) -> rx.Observable[Tuple[VideoFrame, VideoFrame]]:
        return obs


