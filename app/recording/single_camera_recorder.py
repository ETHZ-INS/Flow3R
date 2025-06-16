from PySide6.QtCore import QThread

from app.recording.camera.camera import Camera


class SingleCameraRecorder(QThread):
    def __init__(self, app, camera: Camera, camera_id: str):
        super().__init__()

        self.app = app
        self.camera = camera
        self.camera_id = camera_id

    def run(self):
        while True:
            frame = self.camera.grab_frame()
            if frame is None:
                continue

            camera_widget = self.app.camera_widgets[self.camera_id]
            camera_widget.set_image(frame)
