from contextlib import contextmanager
import threading, time
from dataclasses import dataclass, field
from typing import Dict

import torch
from rx.disposable import Disposable

from app.analysis.pose_estimation.yolo_pose_model import YoloPoseModel
from app.config.welfare_recorder_config import WelfareRecorderConfig


@dataclass
class _Entry:
    model: YoloPoseModel
    refcount: int = 0
    last_used: float = field(default_factory=time.time)
    lock: threading.RLock = field(default_factory=threading.RLock)


class PoseModelManager:
    """
    Deduplicates resources by key, keeps refcounts, guarantees close on last release.
    Thread-safe per resource key.
    """

    class Lease(Disposable):
        def __init__(self, cm):
            super().__init__()
            self._cm = cm
            self.model: YoloPoseModel = self._cm.__enter__()
            self._disposed = False

        def dispose(self):
            if not self._disposed:
                self._disposed = True
                self._cm.__exit__(None, None, None)

    def __init__(self, config: WelfareRecorderConfig):
        self._config = config
        self._entries: Dict[tuple, _Entry] = {}
        self._global_lock = threading.RLock()

    @contextmanager
    def acquire(self, model_id: str, device: str = "cuda"):
        with self._global_lock:
            entry = self._entries.get((model_id, device))
            if entry is None:
                self._load_model(model_id, device)
                entry = self._entries[(model_id, device)]

        with entry.lock:
            entry.refcount += 1
        try:
            yield entry.model
        finally:
            with entry.lock:
                entry.refcount -= 1
                entry.last_used = time.time()
                if entry.refcount <= 0:
                    self._unload_model(model_id, device)

    def acquire_disposable(self, model_id: str, device: str = "cuda") -> 'PoseModelManager.Lease':
        """
        Returns a disposable that will close the camera when disposed.
        """
        return PoseModelManager.Lease(self.acquire(model_id, device))

    def _load_model(self, pose_model_id: str, device: str = "cuda"):
        pose_model_config = self._config.pose_models.get(pose_model_id)
        if not pose_model_config:
            raise ValueError(f"Pose model {pose_model_id} not found in config.")
        if not pose_model_config.folder:
            raise ValueError(f"Pose model {pose_model_id} has no folder configured.")
        model = YoloPoseModel.from_folder(pose_model_config.folder, device)
        entry = _Entry(model=model)

        with self._global_lock:
            self._entries[(pose_model_id, device)] = entry

    def _unload_model(self, model_id: str, device: str = "cuda"):
        with self._global_lock:
            entry = self._entries.pop((model_id, device), None)
            if entry is None:
                return

            with entry.lock:
                if entry.refcount > 0:
                    raise ValueError(f"Cannot unload model {model_id} on device {device} while it is still in use.")
                print(f"Unloading model {model_id} on device {device}")
                del entry.model
                torch.cuda.empty_cache()
