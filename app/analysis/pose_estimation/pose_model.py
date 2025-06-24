from typing import List

import numpy as np

from py3r.point_tracking.core.data.instance import Instance
from py3r.point_tracking.core.data.instance_type import InstanceType


class PoseModel:
    def get_instance_types(self) -> List[InstanceType]:
        raise NotImplementedError

    def predict_frame(self, frame: np.ndarray) -> List[Instance]:
        raise NotImplementedError

    def predict_frames(self, frames: List[np.ndarray]) -> List[List[Instance]]:
        return [self.predict_frame(frame) for frame in frames]
