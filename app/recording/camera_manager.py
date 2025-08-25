import threading
from typing import Dict

from app.config.camera_config import CameraConfig
from app.recording.camera.camera_builder import CameraBuilder
from app.recording.camera.camera_source import CameraSource


class Camera:
    def __init__(self):
        self.camera_config: CameraConfig | None = None
        self.camera_source: CameraSource | None = None
        self.error = None
        self.refcount: int = 0

    @property
    def ready(self) -> bool:
        return self.camera_source is not None and self.error is None

    @property
    def in_use(self) -> bool:
        return self.refcount > 0

    def configure(self, camera_config: CameraConfig):
        if self.in_use:
            raise ValueError("Cannot change camera configuration while it is in use.")

        self.camera_config = camera_config

        if not camera_config:
            self.error = "Camera configuration is not set."
            return

        config_error = camera_config.error
        if config_error:
            self.error = config_error
            return

        self.rebuild()

    def rebuild(self):
        if self.in_use:
            raise ValueError("Cannot rebuild camera while it is in use.")

        self.close()

        try:
            self.camera_source = CameraBuilder.build(self.camera_config)
            self.error = None
        except Exception as e:
            self.error = str(e)

    def close(self):
        if self.camera_source is None:
            return
        try:
            self.camera_source.wait(5)  # Ensure the camera source is closed before rebuilding
        except TimeoutError as e:
            self.error = "Failed to close camera source."
            # TODO: Apparently this can happen when there was an error starting the camera.
            raise ValueError(self.error) from e
        except Exception as e:
            self.error = str(e)
            raise


class CameraManager:
    def __init__(self):
        self._cameras: Dict[str, Camera] = {}
        self._global_lock = threading.RLock()

    def add_camera(self, camera_config: CameraConfig, remove_if_exists = False) -> Camera:
        with self._global_lock:
            if camera_config.camera_id in self._cameras:
                if remove_if_exists:
                    self.remove_camera(camera_config.camera_id)
                else:
                    raise ValueError(f"Camera {camera_config.device_key} already exists.")

            camera = Camera()
            camera.configure(camera_config)
            self._cameras[camera_config.camera_id] = camera
            return camera

    def remove_camera(self, camera_id: str):
        with self._global_lock:
            camera = self._cameras.get(camera_id)
            if camera is None:
                return
            if camera.in_use:
                raise ValueError(f"Cannot remove camera {camera_id} while it is in use.")
            camera.close()
            del self._cameras[camera_id]

    def update_camera(self, camera_config: CameraConfig) -> Camera:
        with self._global_lock:
            camera = self._cameras.get(camera_config.camera_id)
            if camera is None:
                raise ValueError(f"Camera {camera_config.camera_id} does not exist.")
            if camera.in_use:
                raise ValueError(f"Cannot update camera {camera_config.camera_id} while it is in use.")
            camera.configure(camera_config)
            return camera

    def get_camera(self, camera_id: str) -> Camera | None:
        with self._global_lock:
            camera = self._cameras.get(camera_id)
            if camera is None:
                return None
            return camera

    def camera_exists(self, camera_id: str) -> bool:
        print("camera_exists Acquiring lock for thread ", threading.current_thread().name, "...")
        with self._global_lock:
            print("camera_exists Acquired lock for thread ", threading.current_thread().name)
            return camera_id in self._cameras
