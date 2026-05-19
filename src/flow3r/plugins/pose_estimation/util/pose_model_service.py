import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Hashable, Union, Tuple

import numpy as np
import torch
from py3r.pose.core.model.composite_pose_model import CompositePoseModel
from py3r.pose.core.types import PoseInstanceType
from py3r.pose.yolo.model.yolo_pose_model import YoloPoseModel
from reactivex.disposable import Disposable

from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelConfig


@dataclass
class _Entry:
    model: Any
    key: Hashable
    refcount: int = 0


class PoseModelLease(Disposable):
    def __init__(self, model: Any, dispose_cb: Callable[[], None]):
        super().__init__()
        self.model = model
        self._dispose_cb = dispose_cb
        self._disposed = False
        self._lock = threading.Lock()

    def dispose(self) -> None:
        with self._lock:
            if self._disposed:
                return
            self._disposed = True
        self._dispose_cb()


class CompositePoseModelLease(PoseModelLease):
    def __init__(self, model: CompositePoseModel, leases: List[PoseModelLease]):
        def _dispose():
            for lease in leases:
                lease.dispose()

        super().__init__(model, _dispose)
        self._leases = leases


class PoseModelService:
    def __init__(self):
        self._lock = threading.RLock()
        self._models: Dict[Hashable, _Entry] = {}

    def get_instance_types(self, model_config: Union[PoseEstimationModelConfig, Tuple[PoseEstimationModelConfig, ...]]) -> List[PoseInstanceType]:
        if isinstance(model_config, tuple):
            return [instance_type for config in model_config for instance_type in self.get_instance_types(config)]
        return YoloPoseModel.load_instance_types(Path(model_config.model_identifier))

    def get_model(self, model_config: Union[PoseEstimationModelConfig, Tuple[PoseEstimationModelConfig, ...]]) -> PoseModelLease:
        with self._lock:
            if isinstance(model_config, tuple):
                leases = [self.get_model(config) for config in model_config]
                models = [lease.model for lease in leases]
                return CompositePoseModelLease(CompositePoseModel(models), leases)

            model_key = model_config.key
            if model_key not in self._models:
                model = self._build_model(model_config)
                self._models[model_key] = _Entry(model, model_key)
            entry = self._models[model_key]
            entry.refcount += 1
            return PoseModelLease(entry.model, lambda: self._release_model(entry.key))

    def _release_model(self, model_key: Hashable):
        with self._lock:
            entry = self._models[model_key]
            entry.refcount -= 1
            if entry.refcount == 0:
                self._teardown_model(entry)
                del self._models[model_key]

    def _build_model(self, model_config: PoseEstimationModelConfig) -> Any:
        model = YoloPoseModel.from_folder(Path(model_config.model_identifier))
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        model.predict(dummy)  # Make sure the model is initialized and fused
        return model

    def _teardown_model(self, entry: _Entry):
        del entry.model
        import gc
        gc.collect()
        torch.cuda.empty_cache()
