from app.config.camera_config import CameraConfig
from app.recording.camera.pylon_camera_source import PylonCameraSource
from app.recording.camera.video_file_camera_source import VideoFileCameraSource
from app.recording.camera.webcam_camera_source import WebcamCameraSource


class CameraBuilder:
    @classmethod
    def build(cls, camera_config: CameraConfig):
        if camera_config.camera_type == "webcam":
            return WebcamCameraSource(camera_config.webcam.device_index)
        elif camera_config.camera_type == "video_file":
            return VideoFileCameraSource(camera_config.video_file.video_file_path)
        elif camera_config.camera_type == "pylon":
            return PylonCameraSource(camera_config.pylon.device_name,
                                     config_file=camera_config.pylon.get_config_file_path())
        else:
            raise ValueError(f"Unknown camera type: {camera_config.camera_type}")