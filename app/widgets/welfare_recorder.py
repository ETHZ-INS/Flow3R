import cv2
from PySide6 import QtCore
from PySide6.QtWidgets import QMainWindow

from app.layout.welfare_recorder import Ui_WelfareRecorder
from app.recording.camera.video_file_camera import VideoFileCamera
from app.recording.single_camera_recorder import SingleCameraRecorder
from app.widgets.camera_configuration_dialog import CameraConfigurationDialog
from app.widgets.camera_widget import CameraWidget
from app.widgets.welfare_analysis_widget import WelfareAnalysisWidget


class WelfareRecorder(Ui_WelfareRecorder, QMainWindow):
    def __init__(self):
        super(WelfareRecorder, self).__init__()

        self.setupUi(self)

        self.cameras = {}
        self.camera_widgets = {}
        self.recorders = {}

        self.example_image = cv2.imread("C:/Users/Me/Pictures/vlcsnap-2023-10-19-15h03m08s429.png")

        self.action_configure_cameras.triggered.connect(self.configure_cameras)

        welfare_analysis_widget = WelfareAnalysisWidget()
        welfare_analysis_widget.setObjectName("welfare_analysis_widget")
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, welfare_analysis_widget)

        self.state = None

    def configure_cameras(self):
        dialog = CameraConfigurationDialog(self.cameras, parent=self)
        dialog.setWindowTitle("Configure Cameras")
        dialog.setModal(True)

        if dialog.exec():
            self.cameras = dialog.cameras
            self.update_camera_widgets()
        else:
            print("Camera configuration cancelled.")

    def update_camera_widgets(self):
        cameras_to_remove = set(self.camera_widgets.keys()) - set(self.cameras.keys())
        cameras_to_add = set(self.cameras.keys()) - set(self.camera_widgets.keys())

        for camera_id in cameras_to_remove:
            if camera_id in self.camera_widgets:
                widget = self.camera_widgets.pop(camera_id, None)
                if widget:
                    widget.deleteLater()

        for camera_id in cameras_to_add:
            widget = CameraWidget(self.cameras[camera_id].camera_name)
            widget.setObjectName(camera_id)
            self.camera_widgets[camera_id] = widget
            self.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, widget)

        for camera_id in self.cameras.keys():
            widget = self.camera_widgets.get(camera_id)
            if widget:
                widget.camera_name = self.cameras[camera_id].camera_name
                widget.setWindowTitle(widget.camera_name)
                widget.set_image(self.example_image)
            else:
                print(f"Camera {camera_id} not found in camera widgets.")

    def keyPressEvent(self, event, /):
        if event.key() == QtCore.Qt.Key.Key_S:
            for camera_id, camera_config in self.cameras.items():
                camera = VideoFileCamera(camera_config.video_file.video_file_path)
                recorder = SingleCameraRecorder(self, camera, camera_config.camera_name)
                self.recorders[camera_config.camera_id] = recorder
                recorder.start()