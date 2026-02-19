import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

import torch
from py3r.pose.core.types import PoseInstanceType
from py3r.pose.yolo.model.yolo_pose_model import YoloPoseModel
from reactivex.disposable import Disposable

from aaaflow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelConfig


@dataclass
class _Entry:
    model: Any
    id: str
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


class PoseModelService:
    def __init__(self):
        self._lock = threading.Lock()
        self._models: Dict[str, _Entry] = {}

    def get_instance_types(self, model_config: PoseEstimationModelConfig) -> List[PoseInstanceType]:
        return YoloPoseModel.load_instance_types(Path(model_config.model_identifier))

    def get_model(self, model_config: PoseEstimationModelConfig) -> PoseModelLease:
        with self._lock:
            if model_config.id not in self._models:
                model = self._build_model(model_config)
                self._models[model_config.id] = _Entry(model, model_config.id)
            entry = self._models[model_config.id]
            entry.refcount += 1
            return PoseModelLease(entry.model, lambda: self._release_model(entry.id))

    def _release_model(self, model_id: str):
        with self._lock:
            entry = self._models[model_id]
            entry.refcount -= 1
            if entry.refcount == 0:
                self._teardown_model(entry.model)
                del self._models[model_id]

    def _build_model(self, model_config: PoseEstimationModelConfig) -> Any:
        return YoloPoseModel.from_folder(Path(model_config.model_identifier))

    def _teardown_model(self, model: Any):
        del model
        import gc
        gc.collect()
        torch.cuda.empty_cache()
