from typing import List

import numpy as np

from py3r.point_tracking.core.data.instance import Instance
from py3r.point_tracking.core.data.instance_type import InstanceType

from app.analysis.pose_estimation.pose_model import PoseModel


class CompositePoseModel(PoseModel):
    def __init__(self, models: List[PoseModel]):
        self._models = models
        # All models must use different class names so instance ids are unique
        # TODO: Is there a way to ensure this?

        ## Letters a to z for model prefixes (max 26 models i guess)
        #self.model_prefixes = [chr(ord('a') + i) for i in range(len(models))]

    def get_instance_types(self) -> List[InstanceType]:
        instance_types = []
        for model in self._models:
            instance_types.extend(model.get_instance_types())
        return instance_types

    def predict_frame(self, frame: np.ndarray) -> List[Instance]:
        instances = []
        for model in self._models:
            instances.extend(model.predict_frame(frame))
        return instances

    def predict_frames(self, frames: List[np.ndarray]) -> List[List[Instance]]:
        instances = [[] for _ in range(len(frames))]

        for model in self._models:
            model_instances = model.predict_frames(frames)
            for i, instance_list in enumerate(model_instances):
                instances[i].extend(instance_list)

        return instances