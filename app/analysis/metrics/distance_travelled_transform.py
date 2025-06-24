from typing import List

from py3r.point_tracking.core.data.instance import Instance
from rx import Observable
import rx.operators as ops


class DistanceTravelledTransform:
    """Callable object: upstream Observable -> downstream Observable."""
    def __init__(self):
        self.distance_travelled = 0.0
        self.last_points = {}

    def update_distances(self, instances: List[Instance]):
        for instance in instances:
            if instance.id not in self.last_points:
                self.last_points[instance.id] = instance.points[5]
            else:
                last_point = self.last_points[instance.id]
                current_point = instance.points[5]
                distance = ((last_point.x - current_point.x) ** 2 + (last_point.y - current_point.y) ** 2) ** 0.5
                self.distance_travelled += distance
                self.last_points[instance.id] = current_point
        return self.distance_travelled

    def __call__(self, upstream: Observable) -> Observable:
        return upstream.pipe(
            ops.map(self.update_distances),
        )
