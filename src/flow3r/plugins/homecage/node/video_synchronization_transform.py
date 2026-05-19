from typing import Tuple, List

import reactivex as rx
from reactivex import operators as ops

from py3r.media.types import VideoFrame

from flow3r.core.streaming.abc.transform import Transform
from flow3r.plugins.core.typing.video import VideoFormat


def sync_by_timestamp(cam_a, cam_b, tol: float):
    """
    cam_a, cam_b: Observable[VideoFrame]
    tol: allowed timestamp difference (same units as VideoFrame.ts)
    returns: Observable[Tuple[VideoFrame, VideoFrame]]
    """

    def try_match(a_q: List[VideoFrame], b_q: List[VideoFrame]) -> Tuple[List[Tuple[VideoFrame, VideoFrame]], List[VideoFrame], List[VideoFrame]]:
        out = []

        # Keep trying while both sides have frames
        while a_q and b_q:
            a = a_q[0]
            b = b_q[0]
            dt = a.timestamp - b.timestamp

            if abs(dt) <= tol:
                # Matched!
                out.append((a, b))
                a_q.pop(0)
                b_q.pop(0)
            elif dt < -tol:
                # a is too early (older). Drop/advance a.
                a_q.pop(0)
            else:
                # b is too early (older). Drop/advance b.
                b_q.pop(0)

        return out, a_q, b_q

    # Tag frames by source, merge into one stream, and keep state
    tagged = rx.merge(
        cam_a.pipe(ops.map(lambda f: ("a", f))),
        cam_b.pipe(ops.map(lambda f: ("b", f))),
    )

    def accumulator(state, item):
        a_q, b_q = state
        side, frame = item
        if side == "a":
            a_q.append(frame)
        else:
            b_q.append(frame)

        matched, a_q, b_q = try_match(a_q, b_q)
        return a_q, b_q, matched

    return tagged.pipe(
        ops.scan(lambda s, item: accumulator((s[0], s[1]), item), seed=([], [], [])),
        ops.flat_map(lambda s: rx.from_iterable(s[2])),  # emit all matched pairs
    )


class VideoSynchronizationTransform(Transform[VideoFormat, Tuple[VideoFrame, VideoFrame], VideoFormat, Tuple[VideoFrame, VideoFrame]]):
    def __init__(self):
        pass

    def setup(self, desc_in: VideoFormat) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def infer_format(self, desc_in: VideoFormat) -> VideoFormat:
        return desc_in

    def transform_observable(self, obs: rx.Observable[Tuple[VideoFrame, VideoFrame]]) -> rx.Observable[Tuple[VideoFrame, VideoFrame]]:
        return obs
