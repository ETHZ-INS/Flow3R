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
from app.config.welfare_recorder_config import WelfareRecorderConfig
from app.recording.adaptive_smoother import adaptive_smoother
from app.recording.camera.pylon_camera_source import PylonCameraSource
from app.recording.camera.video_file_camera_source import VideoFileCameraSource
from app.recording.video_file_sink import VideoFileSink


mouse_model_folder = Path("D:/Experiments/UnifiedTrackingModel/ActualProperSplit/MouseV5_2_HQAmp2")
mouse_model = YoloPoseModel.from_folder(mouse_model_folder)
pose_estimator = PoseEstimationTransform(mouse_model, batch_size=4)


class Recording:
    def __init__(self, recording_id: str, sources: list, preview_branches: list, recording_branches: list):
        self.recording_id = recording_id
        self.sources = sources
        self.sinks = sinks

        self.running = False

    def start(self):
        if self.running:
            print(f"Recording {self.recording_id} is already running.")
            return

        self.running = True
        for source in self.sources:
            source.start()

    def stop(self):
        if not self.running:
            print(f"Recording {self.recording_id} is not running.")
            return

        self.running = False
        for source in self.sources:
            source.stop()

    def dispose(self):
        if self.running:
            self.stop()
        for source in self.sources:
            source.dispose()
        for sink in self.sinks:
            sink.dispose()


class RecordingController(QObject):
    def __init__(self, gui):
        super().__init__(gui)
        self._gui = gui

        self.config = WelfareRecorderConfig()

        self._recordings = {}

    def prepare_recording(self, recording_id: str):
        if recording_id in self._recordings:
            if self._recordings[recording_id].running:
                print(f"Recording {recording_id} is already running.")
                return
            else:


        cameras = [c for c in self.config.cameras.values() if c.recording_id == recording_id]
        pipeline = self._build_pipeline(cameras)
        recording = Recording(recording_id, pipeline)
        self._recordings[recording_id] = recording

    def start_recording(self, recording_id: str):
        self.running = True
        for source in self._pipelines[recording_id]:
            source.start()

    def _build_pipeline(self, camera_configs: List[CameraConfig] = None):
        if camera_configs is None:
            camera_configs = []

        pipeline = []
        for c in camera_configs:
            renderer = PoseRenderTransform()
            heatmapper = PositionHeatmapTransform(1280, 1024)
            distance_measurer = DistanceTravelledTransform()
            smoother = adaptive_smoother(0.1, 1/30)

            camera_source = self._build_camera_source(c)
            pipeline.append(camera_source)

            video_file_sink = self._build_video_file_sink(c)
            preview_sink = self._gui.get_camera_widget(c.camera_id, c)

            frames = camera_source.stream

            video_file_sink.attach(frames)

            poses = frames.pipe(
                pose_estimator,
                smoother,
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

            heatmap_widget = self._gui.get_heatmap_widget(c.camera_id)
            heatmap_widget.attach(heatmaps)

            distances = poses.pipe(
                distance_measurer,
                ops.share()
            )
            distance_widget = self._gui.get_welfare_analysis_widget(c.camera_id)
            distance_widget.attach(distances)
        return pipeline

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
