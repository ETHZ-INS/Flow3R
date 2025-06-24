import cv2
from PySide6 import QtCore
from PySide6.QtWidgets import QMainWindow, QMenu


from app.config.recording_config import RecordingConfig
from app.config.welfare_recorder_config import WelfareRecorderConfig
from app.layout.welfare_recorder import Ui_WelfareRecorder
from app.recording.recording_controller import RecordingController
from app.widgets.camera_configuration_dialog import CameraConfigurationDialog
from app.widgets.camera_widget import CameraWidget
from app.widgets.heatmap_widget import HeatmapWidget
from app.widgets.recording_configuration_dialog import RecordingConfigurationDialog
from app.widgets.welfare_analysis_widget import WelfareAnalysisWidget


class WelfareRecorder(Ui_WelfareRecorder, QMainWindow):
    def __init__(self):
        super(WelfareRecorder, self).__init__()

        self.setupUi(self)

        self.config = WelfareRecorderConfig()
        self.camera_widgets = {}

        self.example_image = cv2.imread("C:/Users/Me/Pictures/vlcsnap-2023-10-19-15h03m08s429.png")

        self.action_configure_cameras.triggered.connect(self.configure_cameras)
        self.action_configure_recordings.triggered.connect(self.configure_recordings)
        self.btn_record.clicked.connect(self.start_recording)

        self.welfare_analysis_widget = WelfareAnalysisWidget()
        self.welfare_analysis_widget.setObjectName("welfare_analysis_widget")
        self.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, self.welfare_analysis_widget)

        self.heatmap_widget = HeatmapWidget()
        self.heatmap_widget.setObjectName("heatmap_widget")
        self.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, self.heatmap_widget)

        self.recording_controller = RecordingController(self)

    def get_welfare_analysis_widget(self):
        return self.welfare_analysis_widget

    def get_heatmap_widget(self):
        return self.heatmap_widget

    def get_camera_widget(self, camera_id: str):
        return self.camera_widgets.get(camera_id, None)

    def configure_cameras(self, camera_id: str = None):
        dialog = CameraConfigurationDialog(self.config.cameras, parent=self, selected_camera_id=camera_id, recording_configs=self.config.recordings)
        dialog.setWindowTitle("Configure Cameras")
        dialog.setModal(True)

        if dialog.exec():
            self.config.cameras = dialog.cameras
            self.update_camera_widgets()
        else:
            print("Camera configuration cancelled.")

    def configure_recordings(self, recording_id: str = None):
        dialog = RecordingConfigurationDialog(self.config.default_recording, self.config.recordings, parent=self, selected_recording_id=recording_id)
        dialog.setWindowTitle("Configure Recordings")
        dialog.setModal(True)

        if dialog.exec():
            self.config.default_recording = dialog.default_recording
            self.config.recordings = dialog.recordings
            self.update_camera_widgets()
        else:
            print("Recording configuration cancelled.")

    def update_camera_widgets(self):
        cameras_to_remove = set(self.camera_widgets.keys()) - set(self.config.cameras.keys())
        cameras_to_add = set(self.config.cameras.keys()) - set(self.camera_widgets.keys())

        for camera_id in cameras_to_remove:
            if camera_id in self.camera_widgets:
                widget = self.camera_widgets.pop(camera_id, None)
                if widget:
                    widget.deleteLater()

        for camera_id in cameras_to_add:
            camera_config = self.config.cameras[camera_id]
            recording_name = self.config.recordings[camera_config.recording_id].recording_name if camera_config.recording_id else None

            widget = CameraWidget()
            widget.setObjectName(f"camera_widget_{camera_id}")
            widget.set_camera_config(camera_config, recording_name)
            widget.configure_camera_signal.connect(self.configure_cameras)
            widget.configure_recording_signal.connect(self.configure_recordings)
            self.camera_widgets[camera_id] = widget
            self.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, widget)

        for camera_id in self.config.cameras.keys():
            widget = self.camera_widgets.get(camera_id)
            if widget:
                camera_config = self.config.cameras[camera_id]
                recording_name = self.config.recordings[camera_config.recording_id].recording_name if camera_config.recording_id else None
                widget.set_camera_config(camera_config, recording_name)
            else:
                print(f"Camera {camera_id} not found in camera widgets.")

    def start_recording(self):
        if not self.recording_controller.running:
            self.recording_controller.prepare_recording(list(self.config.cameras.values()), main_camera_id=list(self.config.cameras.keys())[0])
            self.recording_controller.start_recording()
