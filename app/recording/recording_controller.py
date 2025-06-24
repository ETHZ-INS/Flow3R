from pathlib import Path
from typing import List

from PySide6.QtCore import QObject

from rx import operators as ops

from app.analysis.metrics.distance_travelled_transform import DistanceTravelledTransform
from app.analysis.pose_estimation.pose_estimation_transform import PoseEstimationTransform
from app.analysis.pose_estimation.yolo_pose_model import YoloPoseModel
from app.analysis.visualization.pose_render_transform import PoseRenderTransform
from app.analysis.visualization.position_heatmap_transform import PositionHeatmapTransform
from app.config.camera_config import CameraConfig
from app.recording.pylon_camera_source import PylonCameraSource
from app.recording.video_file_camera_source import VideoFileCameraSource
from app.recording.video_file_sink import VideoFileSink


mouse_model_folder = Path("D:/Experiments/UnifiedTrackingModel/ActualProperSplit/MouseV5_2_HQAmp2")
mouse_model = YoloPoseModel.from_folder(mouse_model_folder)
pose_estimator = PoseEstimationTransform(mouse_model, batch_size=1)
renderer = PoseRenderTransform()
heatmapper = PositionHeatmapTransform(1280, 1024)
distance_measurer = DistanceTravelledTransform()


class RecordingController(QObject):
    def __init__(self, gui):
        super().__init__(gui)
        self._gui = gui

        self._camera_sources = {}
        self._sinks = {}

        self.running = False

    def prepare_recording(self, camera_configs: List[CameraConfig] = None, main_camera_id: str = None):
        if camera_configs is None:
            camera_configs = []
        self._build_pipeline(camera_configs, main_camera_id)

    def start_recording(self):
        self.running = True
        for camera_source in self._camera_sources.values():
            camera_source.start()

    def _build_pipeline(self, camera_configs: List[CameraConfig] = None, main_camera_id: str = None):
        if camera_configs is None:
            camera_configs = []

        for c in camera_configs:
            camera_source = self._build_camera_source(c)
            self._camera_sources[c.camera_id] = camera_source

            video_file_sink = self._build_video_file_sink(c)
            preview_sink = self._gui.get_camera_widget(c.camera_id)

            frames = camera_source.stream

            video_file_sink.attach(frames)

            if c.camera_id == main_camera_id:
                poses = frames.pipe(
                    pose_estimator,
                    ops.share(),
                )

                pose_frames = poses.pipe(
                    ops.zip(frames),
                    ops.map(lambda t_f: (t_f[1], t_f[0])),
                    renderer
                )

                preview_sink.attach(pose_frames)

                heatmaps = poses.pipe(
                    heatmapper,
                    ops.share()
                )

                heatmap_widget = self._gui.get_heatmap_widget()
                heatmap_widget.attach(heatmaps)

                distances = poses.pipe(
                    distance_measurer,
                    ops.share()
                )
                distance_widget = self._gui.get_welfare_analysis_widget()
                distance_widget.attach(distances)
            else:
                preview_sink.attach(frames)

    def _build_camera_source(self, camera_config: CameraConfig):
        print(f"Building camera source for {camera_config.camera_name} ({camera_config.camera_type})")
        if camera_config.camera_type == "video_file":
            return VideoFileCameraSource(camera_config.video_file.video_file_path)
        elif camera_config.camera_type == "webcam":
            raise NotImplementedError("Webcam camera source is not implemented yet.")
        elif camera_config.camera_type == "pylon":
            return PylonCameraSource(camera_config.pylon.device_name, camera_config.pylon.get_config_file_path())

    def _build_video_file_sink(self, camera_config: CameraConfig):
        target_folder = Path("data/recordings")
        target_folder.mkdir(parents=True, exist_ok=True)
        video_file = target_folder / f"{camera_config.camera_name}.mp4"
        sink = VideoFileSink(video_file)
        return sink
