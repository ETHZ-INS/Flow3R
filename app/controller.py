import threading
from concurrent.futures import Future
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import yaml
from PySide6.QtCore import QObject, QThread, Signal, QTimer
from rx.disposable import CompositeDisposable
from rx.subject import Subject
from rx import operators as ops

from app.analysis.pose_estimation.composite_pose_model import CompositePoseModel
from app.analysis.pose_estimation.pose_estimation_transform import PoseEstimationTransform
from app.config.camera_config import CameraConfig
from app.config.pipeline_config import PipelineConfig
from app.config.recording_config import RecordingConfig
from app.config.welfare_recorder_config import WelfareRecorderConfig
from app.recording.camera_manager_3 import CameraManager
from app.recording.camera_widget_image_sink import CameraWidgetImageSink
from app.recording.camera_widget_time_sink import CameraWidgetTimeSink
from app.recording.fps_warning_transform import FPSWarningTransform
from app.recording.pose_model_manager import PoseModelManager
from app.recording.pose_results_sink import PoseResultsSink
from app.recording.relative_time_transform import RelativeTimeTransform
from app.recording.timed_action_transform import TimedActionTransform
from app.recording.video_file_sink import VideoFileSink
from app.recording.widget_manager import WidgetManager
from app.thread_bound_callable import thread_bound


@dataclass(frozen=True)
class ConfigChangeResult:
    success: bool
    message: str = ""


class Recording:
    def __init__(self, start: Subject, stop: Subject, disposable: CompositeDisposable, drains):
        self._start = start
        self._stop = stop
        self._disposable = disposable

        self._drains = drains
        self._drains_finished = 0

        for drain in self._drains:
            drain.add_done_callback(self._drain_finished)

        self.result = Future()

        self.started = False
        self.stopped = False

        self.lock = threading.Lock()

    def start(self):
        if self.started or self.stopped:
            return
        self.started = True
        self._start.on_next(None)

    def stop(self):
        if self.stopped:
            return
        self.stopped = True
        self._stop.on_next(None)

    def dispose(self):
        if self._disposable:
            self._disposable.dispose()
            self._disposable = None

    def _drain_finished(self, future: Future):
        with self.lock:
            self._drains_finished += 1
            if not self.result.done():
                if future.exception():
                    self.result.set_exception(future.exception())
                elif self._drains_finished == len(self._drains):
                    self.result.set_result(None)


class Controller(QObject):
    camera_added = Signal(CameraConfig)  # camera_config
    camera_removed = Signal(str)  # camera_id
    camera_updated = Signal(CameraConfig, CameraConfig)  # new_camera_config, old_camera_config
    camera_activated = Signal(str, bool)

    recording_added = Signal(RecordingConfig)
    recording_removed = Signal(str)  # recording_id
    recording_updated = Signal(RecordingConfig, RecordingConfig)  # new_recording_config, old_recording_config

    camera_assignment_changed = Signal(str, str, str)  # camera_id, new_recording_id, old_recording_id

    recording_state_changed = Signal(str, str)  # recording_id, state
    recording_name_changed = Signal(str, str)  # recording_id, new_name

    def __init__(self, widget_manager: WidgetManager):
        super().__init__()

        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.setObjectName("ControllerThread")
        self._thread.start()

        self.config = WelfareRecorderConfig()

        self.camera_manager = CameraManager()
        self.pose_model_manager = PoseModelManager(self.config)
        self.widget_manager = widget_manager

        self.pose_model_leases = {}

        self.preview_subs = {}
        self.recordings = {}

    @thread_bound(timeout_ms=2000)
    def add_camera(self, camera_config: CameraConfig):
        if camera_config.camera_id in self.config.camera_config_list.cameras:
            return ConfigChangeResult(success=False, message="Camera already exists.")

        self.config.camera_config_list.cameras[camera_config.camera_id] = camera_config
        if camera_config.camera_id not in self.config.pipeline_config_list.pipelines:
            self.config.pipeline_config_list.pipelines[camera_config.camera_id] = PipelineConfig(camera_config.camera_id)
        self.setup_camera.future(camera_config.camera_id)
        self.setup_recording_controls.future()

        QTimer.singleShot(0, lambda: self.camera_added.emit(camera_config))
        return ConfigChangeResult(success=True, message="Camera added successfully.")

    @thread_bound(timeout_ms=2000)
    def remove_camera(self, camera_id: str):
        camera_config = self.config.camera_config_list.cameras.get(camera_id)

        if not camera_config:
            return ConfigChangeResult(success=False, message="Camera not found.")

        if camera_id in self.recordings or camera_config.recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        try:
            self.teardown_camera(camera_id)  # Synchronously, because we need to ensure the camera is removed before deleting the config
            if camera_id in self.config.camera_config_list.cameras:
                del self.config.camera_config_list.cameras[camera_id]
            self.setup_recording_controls()
        except Exception as e:
            print(f"Error removing camera: {e}")
            return ConfigChangeResult(success=False, message=str(e))

        QTimer.singleShot(0, lambda: self.camera_removed.emit(camera_id))
        return ConfigChangeResult(success=True, message="Camera removed successfully.")

    @thread_bound(timeout_ms=2000)
    def update_camera(self, camera_config: CameraConfig):
        if camera_config.camera_id not in self.config.camera_config_list.cameras:
            return ConfigChangeResult(success=False, message="Camera not found.")

        old_config = deepcopy(self.config.camera_config_list.cameras[camera_config.camera_id])
        if camera_config.camera_id in self.recordings or old_config.recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        if camera_config.recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Cannot assign camera to group that is currently running.")

        self.config.camera_config_list.cameras[camera_config.camera_id] = camera_config

        camera = self.camera_manager.get_camera(camera_config.camera_id)
        if not camera or old_config.active_config != camera_config.active_config:
            print(f"Camera {camera_config.camera_id} has changed, rebuilding.")
            self.setup_camera.future(camera_config.camera_id)
        elif old_config.camera_name != camera_config.camera_name or old_config.recording_id != camera_config.recording_id:
            print(f"Camera name or recording ID has changed for {camera_config.camera_id}, updating widgets.")
            self.get_camera_widget(camera_config)

        if old_config.recording_id != camera_config.recording_id:
            self.setup_recording_controls.future()

        QTimer.singleShot(0, lambda: self.camera_updated.emit(camera_config, old_config))
        if old_config.activated != camera_config.activated:
            QTimer.singleShot(0, lambda: self.camera_activated.emit(camera_config.camera_id, camera_config.activated))
        if old_config.recording_id != camera_config.recording_id:
            QTimer.singleShot(0, lambda: self.camera_assignment_changed.emit(camera_config.camera_id, camera_config.recording_id, old_config.recording_id))
        return ConfigChangeResult(success=True, message="Camera updated successfully.")

    @thread_bound(timeout_ms=2000)
    def set_camera_activated(self, camera_id: str, activated: bool):
        if camera_id not in self.config.camera_config_list.cameras:
            return ConfigChangeResult(success=False, message="Camera not found.")

        camera_config = self.config.camera_config_list.cameras[camera_id]
        if camera_id in self.recordings or camera_config.recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        old_camera_config = deepcopy(camera_config)
        camera_config.activated = activated

        if activated:
            self.setup_camera.future(camera_id)
        else:
            print(f"Tearing down camera {camera_id}")
            self.teardown_camera.future(camera_id)

        self.setup_recording_controls.future()

        QTimer.singleShot(0, lambda: self.camera_updated.emit(camera_config, old_camera_config))
        QTimer.singleShot(0, lambda: self.camera_activated.emit(camera_id, activated))
        return ConfigChangeResult(success=True, message="Camera activation changed successfully.")

    @thread_bound(timeout_ms=2000)
    def update_pipeline(self, pipeline_config: PipelineConfig):
        if pipeline_config.camera_id not in self.config.pipeline_config_list.pipelines:
            return ConfigChangeResult(success=False, message="Pipeline not found.")


        camera_config = self.config.camera_config_list.cameras.get(pipeline_config.camera_id)
        if pipeline_config.camera_id in self.recordings or camera_config.recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        self.config.pipeline_config_list.pipelines[pipeline_config.camera_id] = pipeline_config
        self.update_model_leases.future()
        return ConfigChangeResult(success=True, message="Pipeline updated successfully.")

    @thread_bound(timeout_ms=2000)
    def update_model_leases(self):
        pose_models_in_use = set()
        for pipeline_config in self.config.pipeline_config_list.pipelines.values():
            if pipeline_config.pose_estimation:
                for pose_model_config in pipeline_config.pose_estimation_config.models.values():
                    pose_models_in_use.add((pose_model_config.internal_model_name, pose_model_config.device))

        for pose_model_key, lease in list(self.pose_model_leases.items()):
            if pose_model_key not in pose_models_in_use:
                print(f"Releasing pose model lease for {pose_model_key}")
                lease.dispose()
                del self.pose_model_leases[pose_model_key]

        for pose_model_key in pose_models_in_use:
            if pose_model_key not in self.pose_model_leases:
                print(f"Acquiring pose model lease for {pose_model_key}")
                lease = self.pose_model_manager.acquire_disposable(*pose_model_key)
                self.pose_model_leases[pose_model_key] = lease

    @thread_bound(timeout_ms=2000)
    def add_recording(self, recording_config: RecordingConfig):
        if recording_config.recording_id in self.config.recording_config_list.recordings:
            return ConfigChangeResult(success=False, message="Recording already exists.")

        self.config.recording_config_list.recordings[recording_config.recording_id] = recording_config
        QTimer.singleShot(0, lambda: self.recording_added.emit(recording_config))
        return ConfigChangeResult(success=True, message="Recording added successfully.")

    @thread_bound(timeout_ms=2000)
    def remove_recording(self, recording_id: str):
        if recording_id not in self.config.recording_config_list.recordings:
            return ConfigChangeResult(success=False, message="Group not found.")

        if recording_id == "default":
            return ConfigChangeResult(success=False, message="Cannot remove default group.")

        if recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Recording is currently running or prepared to run.")

        camera_configs = [camera for camera in self.config.camera_config_list.cameras.values() if camera.recording_id == recording_id]
        if len(camera_configs) > 0:
            return ConfigChangeResult(success=False, message="Group is not empty, remove cameras first.")

        del self.config.recording_config_list.recordings[recording_id]
        QTimer.singleShot(0, lambda: self.recording_removed.emit(recording_id))
        return ConfigChangeResult(success=True, message="Recording removed successfully.")

    @thread_bound(timeout_ms=2000)
    def update_recording(self, recording_config: RecordingConfig):
        if recording_config.recording_id not in self.config.recording_config_list.recordings:
            return ConfigChangeResult(success=False, message="Recording not found.")

        if recording_config.recording_id == "default":
            if any(camera.camera_id in self.recordings for camera in self.config.camera_config_list.cameras.values()):
                return ConfigChangeResult(success=False, message="Recording is currently running or prepared to run.")
        else:
            if recording_config.recording_id in self.recordings:
                return ConfigChangeResult(success=False, message="Recording is currently running or prepared to run.")

        old_config = deepcopy(self.config.recording_config_list.recordings[recording_config.recording_id])
        self.config.recording_config_list.recordings[recording_config.recording_id] = deepcopy(recording_config)

        if old_config.recording_name != recording_config.recording_name:
            self.recording_name_changed.emit(recording_config.recording_id, recording_config.recording_name)

        QTimer.singleShot(0, lambda: self.recording_updated.emit(recording_config, old_config))
        return ConfigChangeResult(success=True, message="Recording updated successfully.")

    @thread_bound(timeout_ms=2000)
    def assign_camera_to_recording(self, camera_id: str, recording_id: str):
        camera_config = self.config.camera_config_list.cameras.get(camera_id)
        if not camera_config:
            return ConfigChangeResult(success=False, message="Camera not found.")

        if recording_id and recording_id not in self.config.recording_config_list.recordings:
            return ConfigChangeResult(success=False, message="Recording not found.")

        if camera_id in self.recordings or camera_config.recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        if recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Cannot assign camera to group that is currently running.")

        old_recording_id = camera_config.recording_id

        if old_recording_id == recording_id:
            return ConfigChangeResult(success=True, message="Camera already assigned to this recording.")

        camera_config.recording_id = recording_id
        self.setup_recording_controls.future()

        QTimer.singleShot(0, lambda: self.camera_updated.emit(camera_config, self.config.camera_config_list.cameras[camera_id]))
        QTimer.singleShot(0, lambda: self.camera_assignment_changed.emit(camera_id, recording_id, old_recording_id))

        return ConfigChangeResult(success=True, message="Camera assigned to recording successfully.")

    @thread_bound(timeout_ms=2000)
    def setup_camera(self, camera_id: str):
        print(f"Setting up camera {camera_id}")
        camera = self.camera_manager.get_camera(camera_id)
        if camera is not None and camera.in_use:
            print(f"Camera {camera_id} is currently in use, cannot set up.")
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        try:
            self.stop_preview(camera_id)

            camera_config = self.config.camera_config_list.cameras[camera_id]
            # First make sure camera widget exists so we at least have a place to display errors
            camera_widget = self.get_camera_widget(camera_config)

            if camera is not None:
                camera.configure(camera_config)
            else:
                if camera_config is None:
                    print(f"Camera config not found for camera {camera_id}.")
                    return ConfigChangeResult(success=False, message="Camera config not found.")
                camera = self.camera_manager.add_camera(camera_config, remove_if_exists=True)

            if camera.error:
                print(f"Error in camera {camera_id}: {camera.error}")
                camera_widget.set_camera_message("Error: " + camera.error, show_retry=True, show_edit=True)
                return ConfigChangeResult(success=False, message="Camera Error: " + camera.error)
            else:
                self.start_preview(camera_config.camera_id)
        except Exception as e:
            print(f"Error setting up camera {camera_id}: {e}")
            return ConfigChangeResult(success=False, message="Exception: " + str(e))

    @thread_bound(timeout_ms=2000)
    def teardown_camera(self, camera_id: str):
        camera = self.camera_manager.get_camera(camera_id)

        if camera and camera.in_use:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        try:
            self.stop_preview(camera_id)
            self.camera_manager.remove_camera(camera_id)
            self.remove_camera_widget(camera_id)
        except Exception as e:
            return ConfigChangeResult(success=False, message=str(e))

        return ConfigChangeResult(success=True, message="Camera teared down successfully.")

    @thread_bound(timeout_ms=5000)
    def camera_error(self, camera_id: str, msg: str):
        self.stop_preview(camera_id)

        camera = self.camera_manager.get_camera(camera_id)
        if camera is not None:
            camera.error = msg

        camera_widget = self.get_camera_widget(camera.camera_config)
        camera_widget.set_camera_message("Error: " + msg, show_retry=True, show_edit=True)

    @thread_bound(timeout_ms=2000)
    def setup_recording_controls(self):
        for recording_config in self.config.recording_config_list.recordings.values():
            if recording_config.recording_id in self.recordings:
                continue

            camera_configs = [camera for camera in self.config.camera_config_list.cameras.values() if camera.activated and camera.recording_id == recording_config.recording_id]
            individual_controls = len(camera_configs) < 2

            for camera_config in camera_configs:
                camera_widget = self.get_camera_widget(camera_config)
                if camera_widget is not None:
                    camera_widget.set_show_controls(individual_controls)

            if individual_controls:
                self.remove_recording_controls_widget(recording_config.recording_id)
            else:
                self.get_recording_controls_widget(recording_config)

        for camera_config in self.config.camera_config_list.cameras.values():
            if camera_config.activated and not camera_config.recording_id:
                camera_widget = self.get_camera_widget(camera_config)
                if camera_widget is not None:
                    camera_widget.set_show_controls(True)

    @thread_bound(timeout_ms=10000)
    def prepare_recording(self, recording_id: str):
        recording_config = self.config.recording_config_list.recordings.get(recording_id)
        if not recording_config:
            if recording_id not in self.config.camera_config_list.cameras:
                raise ValueError(f"No recording configuration found for {recording_id}")
            recording_config = self.config.recording_config_list.recordings.get("default")
            if not recording_config:
                raise ValueError(f"No default recording configuration found")

        camera_configs = [camera for camera in self.config.camera_config_list.cameras.values() if camera.activated and camera.recording_id == recording_id or camera.camera_id == recording_id]

        if not camera_configs:
            raise ValueError(f"No camera configurations found for {recording_id}")

        cameras = [self.camera_manager.get_camera(camera_config.camera_id) for camera_config in camera_configs]
        if any(camera is None or not camera.ready for camera in cameras):
            raise ValueError(f"Not all cameras are ready for recording")

        start = Subject()
        stop = Subject()
        disposable = CompositeDisposable()
        drains = []

        for camera_index, (camera_config, camera) in enumerate(zip(camera_configs, cameras)):
            camera_widget = self.get_camera_widget(camera_config)

            relative_time_transform = RelativeTimeTransform()

            w, h, c = camera.camera_source.get_frame_dimensions()
            fps = camera.camera_source.get_fps()

            frame_ops = [
                ops.skip_until(start),
                ops.take_until(stop),
                FPSWarningTransform(window=300, target_fps=fps),
                relative_time_transform
            ]

            if camera_index == 0 and recording_config.recording_mode == "timed":
                frame_ops.append(TimedActionTransform(
                    duration=recording_config.recording_duration,
                    action=lambda: self.stop_recording.future(recording_id)
                ))

            frame_ops.append(ops.share())
            frames = camera.camera_source.stream.pipe(*frame_ops)

            pipeline_config = self.config.pipeline_config_list.pipelines.get(camera_config.camera_id)
            if pipeline_config.pose_estimation:
                pose_models = []
                for pose_model_config in pipeline_config.pose_estimation_config.models.values():
                    model_lease = self.pose_model_leases.get((pose_model_config.internal_model_name, pose_model_config.device))
                    pose_models.append(model_lease.model)

                pose_model = CompositePoseModel(pose_models)
                pose_estimator = PoseEstimationTransform(pose_model, batch_size=24)

                poses = frames.pipe(
                    pose_estimator,
                    #smoother,
                    FPSWarningTransform(window=300, target_fps=fps),
                    ops.share(),
                )

                target_folder = Path("data/recordings")
                target_folder.mkdir(parents=True, exist_ok=True)
                pose_file = target_folder / f"{camera_config.camera_name}_poses.csv"
                pose_results_sink = PoseResultsSink(pose_file)

                pose_results_sink.attach(poses)
                disposable.add(pose_results_sink)
                drains.append(pose_results_sink.result)

            if camera_index == 0:
                if len(camera_configs) > 1:
                    time_widget = self.get_recording_controls_widget(recording_config)
                else:
                    time_widget = camera_widget.recording_controls

                camera_widget_time_sink = CameraWidgetTimeSink(time_widget)
                camera_widget_time_sink.attach(frames)
                disposable.add(camera_widget_time_sink)

            target_folder = Path("data/recordings")
            target_folder.mkdir(parents=True, exist_ok=True)
            video_file = target_folder / f"{camera_config.camera_name}.mp4"
            video_file_sink = VideoFileSink(video_file, width=w, height=h, fps=fps, codec='mp4v')

            video_file_sink.attach(frames)
            disposable.add(video_file_sink)
            drains.append(video_file_sink.result)

        recording = Recording(
            start=start,
            stop=stop,
            disposable=disposable,
            drains=drains
        )

        recording.result.add_done_callback(lambda result, rid=recording_id: self.recording_done(rid, result))

        self.recordings[recording_id] = recording

    @thread_bound(timeout_ms=10000)
    def start_recording(self, recording_id: str):
        print(f"Starting recording {recording_id}")
        if recording_id not in self.recordings:
            try:
                self.prepare_recording(recording_id)
            except Exception as e:
                import traceback
                print(f"Error preparing recording {recording_id}: {e}")
                traceback.print_exc()
                return ConfigChangeResult(success=False, message=str(e))

        recording = self.recordings[recording_id]
        if recording.started or recording.stopped:
            print(f"Recording {recording_id} is already started or stopped.")
            return ConfigChangeResult(success=False, message="Recording already started or stopped.")

        try:
            recording.start()
            self.recording_state_changed.emit(recording_id, "started")
            return ConfigChangeResult(success=True, message="Recording started successfully.")
        except Exception as e:
            print(f"Error starting recording {recording_id}: {e}")
            return ConfigChangeResult(success=False, message=str(e))

    @thread_bound(timeout_ms=2000)
    def stop_recording(self, recording_id: str):
        if recording_id not in self.recordings:
            return ConfigChangeResult(success=True, message="Recording not found.")

        recording = self.recordings[recording_id]
        if not recording.started or recording.stopped:
            del self.recordings[recording_id]
            return ConfigChangeResult(success=True, message="Recording not started or already stopped.")

        try:
            recording.stop()
            # TODO: Find a way to only delete the recording when all drains are finished
            del self.recordings[recording_id]
            self.recording_state_changed.emit(recording_id, "stopped")
            return ConfigChangeResult(success=True, message="Recording stopped successfully.")
        except Exception as e:
            print(f"Error stopping recording {recording_id}: {e}")
            return ConfigChangeResult(success=False, message=str(e))

    @thread_bound(timeout_ms=10000)
    def recording_done(self, recording_id: str, result: Future):
        exc = result.exception()
        if exc is None:
            print(f"Recording {recording_id} completed successfully.")
            return

        camera_configs = [camera for camera in self.config.camera_config_list.cameras.values() if camera.recording_id == recording_id or camera.camera_id == recording_id]
        for camera_config in camera_configs:
            camera_widget = self.get_camera_widget(camera_config)
            camera_widget.set_status_message(f"Recording stopped: {exc}", status_type="error")

        self.stop_recording.future(recording_id)

    def start_preview(self, camera_id: str):
        if camera_id in self.preview_subs:
            self.stop_preview(camera_id)

        camera = self.camera_manager.get_camera(camera_id)
        if camera is None or not camera.ready:
            return

        camera_widget = self.get_camera_widget(camera.camera_config)

        camera_widget.set_camera_message(None)
        camera_widget_image_sink = CameraWidgetImageSink(camera_widget)
        camera_widget_image_sink.error.connect(lambda msg, cid=camera_id: self.camera_error.future(cid, msg))

        preview_sub = camera.camera_source.stream.subscribe(camera_widget_image_sink)
        self.preview_subs[camera_id] = preview_sub

    def stop_preview(self, camera_id: str):
        if camera_id not in self.preview_subs:
            return

        preview_sub = self.preview_subs[camera_id]
        if preview_sub is not None:
            preview_sub.dispose()
        del self.preview_subs[camera_id]

    def get_camera_widget(self, camera_config: CameraConfig):
        recording_config = self.config.recording_config_list.recordings.get(camera_config.recording_id)

        conf = {
            "type": "camera",
            "camera_id": camera_config.camera_id,
            "recording_id": camera_config.recording_id,
            "camera_name": camera_config.camera_name,
            "recording_name": recording_config.recording_name if recording_config else None
        }

        return self.widget_manager.get_widget("camera_"+camera_config.camera_id, conf)

    def remove_camera_widget(self, camera_id: str):
        self.widget_manager.remove_widget("camera_"+camera_id)

    def get_recording_controls_widget(self, recording_config: RecordingConfig):
        conf = {
            "type": "recording_controls",
            "recording_id": recording_config.recording_id,
            "recording_name": recording_config.recording_name
        }

        return self.widget_manager.get_widget("recording_controls_"+recording_config.recording_id, conf)

    def remove_recording_controls_widget(self, recording_id: str):
        self.widget_manager.remove_widget("recording_controls_"+recording_id)

    @thread_bound(timeout_ms=10000)
    def load_config(self, config_file: Path):
        if not config_file.exists():
            return ConfigChangeResult(success=False, message="Configuration file does not exist.")

        if len(self.recordings) > 0:
            return ConfigChangeResult(success=False, message="Cannot load configuration while recordings are active.")

        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                version = config_data.get("version", "1.0")
                ui_state = config_data.get("ui_state", {})
                config_dict = config_data.get("config", {})
                config = WelfareRecorderConfig.from_dict(config_dict)

            for camera_id in list(self.config.camera_config_list.cameras.keys()):
                self.teardown_camera(camera_id)

            # Remove camera configs then setup recording controls to make sure old widgets are removed
            # There is definitely a better way to do this, but this works for now
            self.config.camera_config_list.cameras.clear()
            self.setup_recording_controls()

            self.config = config

            # Apply changes synchronously, because we need to ensure the cameras are set up before restoring the UI state
            # I guess we could also implement the layout restoration in the widget manager, but this is simpler for now
            for camera_config in self.config.camera_config_list.cameras.values():
                self.setup_camera(camera_config.camera_id)

            self.update_model_leases()
            self.setup_recording_controls()

            return ConfigChangeResult(success=True, message=ui_state)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            import traceback
            traceback.print_exc()
            return ConfigChangeResult(success=False, message=str(e))

    @thread_bound(timeout_ms=10000)
    def save_config(self, config_file: Path, ui_state: dict = None):
        try:
            config_data = {
                "version": "1.0",
                "ui_state": ui_state,
                "config": self.config.to_dict()
            }

            with open(config_file, 'w') as f:
                yaml.safe_dump(config_data, f)

            return ConfigChangeResult(success=True, message="Configuration saved successfully.")
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return ConfigChangeResult(success=False, message=str(e))
