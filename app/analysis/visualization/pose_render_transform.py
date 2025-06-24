import cv2
from rx import Observable
import rx.operators as ops


class PoseRenderTransform:
    """Callable object: upstream Observable -> downstream Observable."""
    def __init__(self):
        pass

    def render_frame(self, frame):
        # Placeholder for rendering logic
        (fn, ts, frame), instances = frame
        frame = frame.copy()
        for instance in instances:
            for point in instance.points:
                if point is None:
                    continue
                frame = cv2.circle(
                    frame,
                    (int(point.x), int(point.y)),
                    radius=2,
                    color=(255.0, 255.0, 255.0),
                    thickness=-1,
                )
        return fn, ts, frame

    def __call__(self, upstream: Observable) -> Observable:
        return upstream.pipe(
            ops.map(self.render_frame),
        )
