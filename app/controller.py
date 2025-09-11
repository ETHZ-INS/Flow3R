import threading
from concurrent.futures import Future
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from PySide6.QtCore import QObject, QThread, Signal, QTimer
from rx.disposable import CompositeDisposable
from rx.subject import Subject
from rx import operators as ops

from app.analysis.pose_estimation.composite_pose_model import CompositePoseModel
from app.analysis.pose_estimation.pose_estimation_transform import PoseEstimationTransform
from app.config.camera_config import CameraConfig
from app.config.pipeline_config import PipelineConfig
from app.config.recording_config import GroupConfig
from app.config.variable_config import VariableConfig, VariableValue
from app.config.welfare_recorder_config import WelfareRecorderConfig, CameraConfigView, GroupConfigView
from app.recording.camera_manager import CameraManager
from app.recording.camera_widget_image_sink import CameraWidgetImageSink
from app.recording.camera_widget_time_sink import CameraWidgetTimeSink
from app.recording.fps_warning_transform import FPSWarningTransform
from app.recording.pose_model_manager import PoseModelManager
from app.recording.pose_results_sink import PoseResultsSink
from app.recording.relative_time_transform import RelativeTimeTransform
from app.recording.timed_action_transform import TimedActionTransform
from app.recording.video_file_sink import VideoFileSink
from app.recording.widget_manager import WidgetManager
from app.recording_state import RecordingState, RecordingStateBase
from app.thread_bound_callable import thread_bound


@dataclass(frozen=True)
class ConfigChangeResult:
    success: bool
    message: str = ""


@dataclass(frozen=True)
class CircularDependency:
    var_name: str
    path: list


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

    recording_added = Signal(GroupConfig)
    recording_removed = Signal(str)  # recording_id
    recording_updated = Signal(GroupConfig, GroupConfig)  # new_recording_config, old_recording_config

    variable_added = Signal(VariableConfig)
    variable_removed = Signal(str)  # variable_name
    variable_updated = Signal(VariableConfig, VariableConfig)  # new_variable_config, old_variable_config

    camera_view_changed = Signal(str, CameraConfigView)  # camera_id, new_view
    group_view_changed = Signal(str, GroupConfigView)  # recording_id, new_view

    camera_assignment_changed = Signal(str, str, str)  # camera_id, new_recording_id, old_recording_id

    recording_state_changed = Signal(str, RecordingStateBase)  # recording_id, state, message
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

        self.cameras_with_widgets = set()
        self.groups_with_controls = set()
        self.cameras_with_controls = set()

    @thread_bound(timeout_ms=2000)
    def get_config(self):
        return deepcopy(self.config)

    @thread_bound(timeout_ms=2000)
    def get_camera_view(self, camera_id: str):
        return deepcopy(self.config.get_camera_view(camera_id))

    @thread_bound(timeout_ms=2000)
    def get_group_view(self, group_id: str):
        return deepcopy(self.config.get_group_view(group_id))

    @thread_bound(timeout_ms=2000)
    def add_camera(self, camera_config: CameraConfig):
        if self.config.cameras.get(camera_config.camera_id):
            return ConfigChangeResult(success=False, message="Camera already exists.")

        self.config.cameras[camera_config.camera_id] = camera_config
        if not self.config.pipelines.get(camera_config.camera_id):
            self.config.pipelines[camera_config.camera_id] = PipelineConfig(camera_config.camera_id)

        self.setup_camera.future(camera_config.camera_id)
        self.setup_recording_controls.future()
        self.check_recording_state.future(camera_config.camera_id if camera_config.recording_id is None else camera_config.recording_id)

        QTimer.singleShot(0, lambda: self.camera_added.emit(camera_config))
        return ConfigChangeResult(success=True, message="Camera added successfully.")

    @thread_bound(timeout_ms=2000)
    def remove_camera(self, camera_id: str):
        camera_view = self.config.get_camera_view(camera_id)

        if not camera_view:
            return ConfigChangeResult(success=False, message="Camera not found.")

        if camera_view.group_id in self.recordings:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        try:
            self.teardown_camera(camera_id)  # Synchronously, because we need to ensure the camera is removed before deleting the config
            if camera_id in self.config.cameras:
                del self.config.cameras[camera_id]
            self.setup_recording_controls()
            self.check_recording_state(camera_view.group_id)
        except Exception as e:
            print(f"Error removing camera: {e}")
            return ConfigChangeResult(success=False, message=str(e))

        QTimer.singleShot(0, lambda: self.camera_removed.emit(camera_id))
        return ConfigChangeResult(success=True, message="Camera removed successfully.")

    @thread_bound(timeout_ms=2000)
    def update_camera(self, camera_config: CameraConfig):
        camera_view = self.config.get_camera_view(camera_config.camera_id)
        if not camera_view:
            return ConfigChangeResult(success=False, message="Camera not found.")

        if camera_view.group_id in self.recordings:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        if camera_config.recording_id and camera_config.recording_id in self.recordings:
            return ConfigChangeResult(success=False, message="Cannot assign camera to group that is currently running.")

        old_config = camera_view.camera
        self.config.cameras[camera_config.camera_id] = camera_config

        camera = self.camera_manager.get_camera(camera_config.camera_id)
        if not camera or old_config.active_config != camera_config.active_config:
            print(f"Camera {camera_config.camera_id} has changed, rebuilding.")
            self.setup_camera.future(camera_config.camera_id)
        elif old_config.camera_name != camera_config.camera_name or old_config.recording_id != camera_config.recording_id:
            print(f"Camera name or recording ID has changed for {camera_config.camera_id}, updating widgets.")
            self.get_camera_widget(camera_config)

        if old_config.recording_id != camera_config.recording_id:
            self.setup_recording_controls.future()

        self.check_recording_state.future(camera_config.camera_id if camera_config.recording_id is None else camera_config.recording_id)

        QTimer.singleShot(0, lambda: self.camera_updated.emit(camera_config, old_config))
        if old_config.activated != camera_config.activated:
            QTimer.singleShot(0, lambda: self.camera_activated.emit(camera_config.camera_id, camera_config.activated))
        if old_config.recording_id != camera_config.recording_id:
            QTimer.singleShot(0, lambda: self.camera_assignment_changed.emit(camera_config.camera_id, camera_config.recording_id, old_config.recording_id))
        return ConfigChangeResult(success=True, message="Camera updated successfully.")

    @thread_bound(timeout_ms=2000)
    def set_camera_activated(self, camera_id: str, activated: bool):
        camera_config = self.config.cameras.get(camera_id)
        if not camera_config:
            return ConfigChangeResult(success=False, message="Camera not found.")
        camera_config.activated = activated
        return self.update_camera(camera_config)

    @thread_bound(timeout_ms=2000)
    def assign_camera_to_recording(self, camera_id: str, recording_id: str):
        camera_config = self.config.cameras.get(camera_id)
        if not camera_config:
            return ConfigChangeResult(success=False, message="Camera not found.")
        camera_config.recording_id = recording_id if recording_id != "default" else None
        return self.update_camera(camera_config)

    @thread_bound(timeout_ms=2000)
    def update_pipeline(self, pipeline_config: PipelineConfig):
        if pipeline_config.camera_id not in self.config.pipelines:
            return ConfigChangeResult(success=False, message="Pipeline not found.")

        camera_view = self.config.get_camera_view(pipeline_config.camera_id)
        if camera_view.group_id in self.recordings:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        self.config.pipelines[pipeline_config.camera_id] = pipeline_config

        self.update_model_leases.future()
        self.check_recording_state.future(camera_view.group_id)
        return ConfigChangeResult(success=True, message="Pipeline updated successfully.")

    @thread_bound(timeout_ms=2000)
    def update_model_leases(self):
        pose_models_in_use = set()
        for pipeline_config in self.config.pipelines.values():
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
    def add_group(self, group_config: GroupConfig):
        if self.config.groups.get(group_config.recording_id):
            return ConfigChangeResult(success=False, message="Group already exists.")

        self.config.groups[group_config.recording_id] = group_config

        self.check_recording_state.future(group_config.recording_id)
        QTimer.singleShot(0, lambda: self.recording_added.emit(group_config))
        return ConfigChangeResult(success=True, message="Group added successfully.")

    @thread_bound(timeout_ms=2000)
    def remove_group(self, group_id: str):
        if group_id == "default":
            return ConfigChangeResult(success=False, message="Cannot remove default group.")

        group_view = self.config.get_group_view(group_id)
        if not group_view:
            return ConfigChangeResult(success=False, message="Group not found.")

        if group_id in self.recordings:
            return ConfigChangeResult(success=False, message="Recording is currently running or prepared to run.")

        if len(group_view.cameras) > 0:
            return ConfigChangeResult(success=False, message="Group is not empty, remove cameras first.")

        del self.config.groups[group_id]

        self.check_recording_state.future(group_id)
        QTimer.singleShot(0, lambda: self.recording_removed.emit(group_id))
        return ConfigChangeResult(success=True, message="Recording removed successfully.")

    @thread_bound(timeout_ms=2000)
    def update_recording(self, group_config: GroupConfig):
        group_view = self.config.get_group_view(group_config.recording_id)
        if not group_view:
            return ConfigChangeResult(success=False, message="Group not found.")

        if group_config.recording_id == "default":
            # TODO: Save a snapshot of the recording config when starting a recording so the default can be changed while recording
            if any(camera.camera_id in self.recordings for camera in self.config.cameras.values()):
                return ConfigChangeResult(success=False, message="Recording is currently running or prepared to run.")
        else:
            if group_config.recording_id in self.recordings:
                return ConfigChangeResult(success=False, message="Recording is currently running or prepared to run.")

        old_config = deepcopy(group_view.group)
        self.config.groups[group_config.recording_id] = group_config

        self.check_recording_state.future(group_config.recording_id)

        QTimer.singleShot(0, lambda: self.recording_updated.emit(group_config, old_config))
        return ConfigChangeResult(success=True, message="Recording updated successfully.")

    @thread_bound(timeout_ms=2000)
    def add_placeholder(self, placeholder_config: VariableConfig):
        if placeholder_config.variable_id in self.config.placeholders:
            return ConfigChangeResult(success=False, message="Placeholder already exists.")

        self.config.placeholders[placeholder_config.variable_id] = placeholder_config
        QTimer.singleShot(0, lambda: self.variable_added.emit(placeholder_config))
        self.refresh_all_group_views.future()
        return ConfigChangeResult(success=True, message="Placeholder added successfully.")

    @thread_bound(timeout_ms=2000)
    def remove_placeholder(self, variable_id: str):
        if variable_id not in self.config.placeholders:
            return ConfigChangeResult(success=False, message="Placeholder not found.")

        del self.config.placeholders[variable_id]
        # TODO: check recording state if needed
        QTimer.singleShot(0, lambda: self.variable_removed.emit(variable_id))
        self.refresh_all_group_views.future()
        return ConfigChangeResult(success=True, message="Placeholder removed successfully.")

    @thread_bound(timeout_ms=2000)
    def update_placeholder(self, placeholder_config: VariableConfig):
        old_placeholder_config = self.config.placeholders.get(placeholder_config.variable_id)
        if not old_placeholder_config:
            return ConfigChangeResult(success=False, message="Placeholder not found.")

        self.config.placeholders[placeholder_config.variable_id] = placeholder_config

        # TODO: check recording state if needed
        QTimer.singleShot(0, lambda: self.variable_updated.emit(placeholder_config, old_placeholder_config))
        self.refresh_all_group_views.future()
        return ConfigChangeResult(success=True, message="Variable updated successfully.")

    @thread_bound(timeout_ms=2000)
    def set_variables_project(self, values: dict[str, Any]):
        print(f"Setting project variables: {values}")
        for variable_id, value in values.items():
            if variable_id not in self.config.values:
                self.config.values[variable_id] = VariableValue(variable_id)
            self.config.values[variable_id].value = value

        self.check_all_recording_states.future()
        self.refresh_all_group_views.future()
        return ConfigChangeResult(success=True, message="Variables updated successfully.")

    @thread_bound(timeout_ms=2000)
    def set_variables_group(self, group_id: str, values: dict[str, Any]):
        print(f"Setting group variables: {values}")
        group_config = self.config.groups.get(group_id)
        if group_config is None:
            camera_config = self.config.cameras.get(group_id)
            if camera_config is None:
                return ConfigChangeResult(success=False, message="Group not found.")
            target_values = camera_config.variable_values
        else:
            target_values = group_config.variable_values

        for variable_id, value in values.items():
            if variable_id not in target_values:
                target_values[variable_id] = VariableValue(variable_id)
            target_values[variable_id].value = value

        self.check_recording_state.future(group_id)
        self.refresh_group_view.future(group_id)
        return ConfigChangeResult(success=True, message="Variables updated successfully.")

    @thread_bound(timeout_ms=2000)
    def set_variables_camera(self, camera_id: str, values: dict[str, Any]):
        print(f"Setting camera variables: {values}")
        camera_config = self.config.cameras.get(camera_id)
        if camera_config is None:
            return ConfigChangeResult(success=False, message="Camera not found.")

        for variable_id, value in values.items():
            if variable_id not in camera_config.variable_values:
                camera_config.variable_values[variable_id] = VariableValue(variable_id)
            camera_config.variable_values[variable_id].value = value

        camera_view = self.config.get_camera_view(camera_id)

        self.check_recording_state.future(camera_view.group_id)
        self.refresh_group_view.future(camera_view.group_id)
        return ConfigChangeResult(success=True, message="Variables updated successfully.")

    @thread_bound(timeout_ms=2000)
    def setup_camera(self, camera_id: str):
        camera_view = self.config.get_camera_view(camera_id)
        if not camera_view:
            print(f"Camera view not found for camera {camera_id}.")
            return ConfigChangeResult(success=False, message="Camera view not found.")

        if camera_view.group_id in self.recordings:
            print(f"Camera {camera_id} is currently in use, cannot set up.")
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        camera = self.camera_manager.get_camera(camera_id)

        try:
            self.stop_preview(camera_id)

            # First make sure camera widget exists so we at least have a place to display errors
            camera_widget = self.get_camera_widget(camera_view.camera)

            if camera is not None:
                camera.configure(camera_view.camera)
            else:
                camera = self.camera_manager.add_camera(camera_view.camera, remove_if_exists=True)

            if camera.error:
                print(f"Error in camera {camera_id}: {camera.error}")
                camera_widget.set_camera_message("Error: " + camera.error, show_retry=True, show_edit=True)
                return ConfigChangeResult(success=False, message="Camera Error: " + camera.error)
            else:
                self.start_preview(camera_id)
        except Exception as e:
            print(f"Error setting up camera {camera_id}: {e}")
            return ConfigChangeResult(success=False, message="Exception: " + str(e))

    @thread_bound(timeout_ms=2000)
    def teardown_camera(self, camera_id: str):
        camera_view = self.config.get_camera_view(camera_id)
        if not camera_view:
            print(f"Camera view not found for camera {camera_id}.")
            return ConfigChangeResult(success=False, message="Camera view not found.")

        if camera_view.group_id in self.recordings:
            print(f"Camera {camera_id} is currently in use, cannot set up.")
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        camera = self.camera_manager.get_camera(camera_id)

        if camera and camera.in_use:
            return ConfigChangeResult(success=False, message="Camera is currently in use.")

        try:
            self.stop_preview(camera_id)
            self.camera_manager.remove_camera(camera_id)
            self.remove_camera_widget(camera_id)
        except Exception as e:
            return ConfigChangeResult(success=False, message=str(e))

        return ConfigChangeResult(success=True, message="Camera torn down successfully.")

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
        groups_with_controls = set()
        for group_config in self.config.groups.values():
            group_view = self.config.get_group_view(group_config.recording_id)
            if len(group_view.cameras) >= 2:
                groups_with_controls.add(group_config.recording_id)

        cameras_with_controls = set()
        for camera_config in self.config.cameras.values():
            if not camera_config.activated:
                print(f"Camera {camera_config.camera_id} is not activated, skipping.")
                continue
            if not camera_config.recording_id or camera_config.recording_id not in groups_with_controls:
                cameras_with_controls.add(camera_config.camera_id)

        for group_id in self.groups_with_controls:
            if group_id not in groups_with_controls:
                self.remove_recording_controls_widget(group_id)
                self.groups_with_controls.remove(group_id)

        for camera_id in list(self.cameras_with_controls):
            if camera_id not in cameras_with_controls:
                camera_config = self.config.cameras.get(camera_id)
                if camera_config:
                    camera_widget = self.get_camera_widget(camera_config)
                    if camera_widget is not None:
                        camera_widget.set_show_controls(False)
                self.cameras_with_controls.remove(camera_id)

        for group_id in groups_with_controls:
            group_config = self.config.groups[group_id]
            recording_controls_widget = self.get_recording_controls_widget(group_config)
            if recording_controls_widget is not None:
                self.groups_with_controls.add(group_id)

        for camera_id in cameras_with_controls:
            camera_config = self.config.cameras.get(camera_id)
            camera_widget = self.get_camera_widget(camera_config)
            if camera_widget is not None:
                camera_widget.set_show_controls(True)
                self.cameras_with_controls.add(camera_id)

    @thread_bound(timeout_ms=2000)
    def reset_non_persistent_variables(self):
        group_configs = list(self.config.groups.values())
        camera_configs = list(self.config.cameras.values())

        value_dicts = [self.config.values] + [c.variable_values for c in group_configs] + [c.variable_values for c in camera_configs]

        for placeholder in self.config.placeholders.values():
            if placeholder.persistence != "forever":
                for target_values in value_dicts:
                    if placeholder.variable_id in target_values:
                        del target_values[placeholder.variable_id]

    @thread_bound(timeout_ms=2000)
    def reset_recording_variables(self, group_id: str):
        group_view = self.config.get_group_view(group_id)
        if not group_view:
            raise ValueError(f"No recording view found for {group_id}")

        group_config = self.config.groups.get(group_id)
        camera_configs = [self.config.cameras[c.camera.camera_id] for c in group_view.cameras if c.camera.camera_id in self.config.cameras]
        if group_config:
            value_dicts = [self.config.values] + [group_config.variable_values] + [c.variable_values for c in camera_configs]
        else:
            value_dicts = [self.config.values] + [c.variable_values for c in camera_configs]

        for placeholder in self.config.placeholders.values():
            if placeholder.persistence == "recording":
                for target_values in value_dicts:
                    if placeholder.variable_id in target_values:
                        del target_values[placeholder.variable_id]

        self.refresh_group_view.future(group_id)
        self.check_recording_state.future(group_id)

    @thread_bound(timeout_ms=10000)
    def prepare_recording(self, group_id: str):
        group_view = self.config.get_group_view(group_id)
        if not group_view:
            return ConfigChangeResult(success=False, message="Recording not found.")

        cameras = [self.camera_manager.get_camera(cv.camera.camera_id) for cv in group_view.cameras]
        if any(camera is None or not camera.ready for camera in cameras):
            raise ValueError(f"Not all cameras are ready for recording")

        start = Subject()
        stop = Subject()
        disposable = CompositeDisposable()
        drains = []

        group_config = group_view.group
        for camera_index, (camera_view, camera) in enumerate(zip(group_view.cameras, cameras)):
            camera_config = camera_view.camera
            pipeline_config = camera_view.pipeline

            placeholder_context = camera_view.placeholder_context
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

            if camera_index == 0 and group_config.recording_mode == "timed":
                frame_ops.append(TimedActionTransform(
                    duration=group_config.recording_duration,
                    action=lambda: self.stop_recording.future(group_id)
                ))

            frame_ops.append(ops.share())
            frames = camera.camera_source.stream.pipe(*frame_ops)

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

                if pipeline_config.pose_estimation_config.save_to_file:
                    pose_file = Path(placeholder_context.format(pipeline_config.pose_estimation_config.save_file))
                    pose_file.parent.mkdir(parents=True, exist_ok=True)
                    pose_results_sink = PoseResultsSink(pose_file)

                    pose_results_sink.attach(poses)
                    disposable.add(pose_results_sink)
                    drains.append(pose_results_sink.result)

            if camera_index == 0:
                if len(cameras) > 1:
                    time_widget = self.get_recording_controls_widget(group_config)
                else:
                    time_widget = camera_widget.recording_controls

                camera_widget_time_sink = CameraWidgetTimeSink(time_widget)
                camera_widget_time_sink.attach(frames)
                disposable.add(camera_widget_time_sink)

            if pipeline_config.save_video:
                video_file = Path(placeholder_context.format(pipeline_config.save_video_config.file_path))
                video_file.parent.mkdir(parents=True, exist_ok=True)
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

        recording.result.add_done_callback(lambda result, rid=group_id: self.recording_done(rid, result))

        self.recordings[group_id] = recording
        return ConfigChangeResult(success=True, message="Recording prepared")

    @thread_bound(timeout_ms=10000)
    def start_recording(self, group_id: str):
        print(f"Starting recording {group_id}")
        if group_id not in self.recordings:
            try:
                self.prepare_recording(group_id)
            except Exception as e:
                import traceback
                print(f"Error preparing recording {group_id}: {e}")
                traceback.print_exc()
                return ConfigChangeResult(success=False, message=str(e))

        recording = self.recordings[group_id]
        if recording.started or recording.stopped:
            print(f"Recording {group_id} is already started or stopped.")
            return ConfigChangeResult(success=False, message="Recording already started or stopped.")

        try:
            recording.start()
            self.check_recording_state.future(group_id)
            return ConfigChangeResult(success=True, message="Recording started successfully.")
        except Exception as e:
            print(f"Error starting recording {group_id}: {e}")
            return ConfigChangeResult(success=False, message=str(e))

    @thread_bound(timeout_ms=2000)
    def stop_recording(self, group_id: str):
        if group_id not in self.recordings:
            return ConfigChangeResult(success=True, message="Recording not found.")

        recording = self.recordings[group_id]
        if not recording.started or recording.stopped:
            del self.recordings[group_id]
            return ConfigChangeResult(success=True, message="Recording not started or already stopped.")

        try:
            recording.stop()
            # TODO: Find a way to only delete the recording when all drains are finished
            del self.recordings[group_id]
            self.reset_recording_variables(group_id)
            self.check_recording_state.future(group_id)
            return ConfigChangeResult(success=True, message="Recording stopped successfully.")
        except Exception as e:
            print(f"Error stopping recording {group_id}: {e}")
            return ConfigChangeResult(success=False, message=str(e))

    @thread_bound(timeout_ms=10000)
    def recording_done(self, group_id: str, result: Future):
        exc = result.exception()
        if exc is None:
            print(f"Recording {group_id} completed successfully.")
            return

        # TODO: Add event log
        group_view = self.config.get_group_view(group_id)
        camera_configs = [self.config.cameras[c.camera.camera_id] for c in group_view.cameras if c.camera.camera_id in self.config.cameras]

        for camera_config in camera_configs:
            camera_widget = self.get_camera_widget(camera_config)
            camera_widget.set_status_message(f"Recording stopped: {exc}", status_type="error")

        self.stop_recording.future(group_id)

    @thread_bound(timeout_ms=2000)
    def get_recording_state(self, group_id: str):
        print(f"Getting recording state for {group_id}")
        if group_id in self.recordings:
            print(f"Recording {group_id} is already started")
            return RecordingState.Running()

        group_view = self.config.get_group_view(group_id)
        if not group_view:
            print(f"Recording {group_id} not found")
            return RecordingState.NotReady("Recording not found")

        cameras = [self.camera_manager.get_camera(cv.camera.camera_id) for cv in group_view.cameras]
        if any(camera is None or not camera.ready for camera in cameras):
            print(f"One or more cameras are not ready for recording {group_id}")
            return RecordingState.NotReady("One or more cameras are not ready")

        missing_placeholders = set()

        for camera_view in group_view.cameras:
            required_variables = camera_view.get_required_placeholders()
            print(f"Required placeholders for {camera_view.camera.camera_id}: {required_variables}")
            placeholder_context = camera_view.placeholder_context

            for variable_name in list(required_variables):
                value = placeholder_context.resolve(variable_name)
                if value.circular_dependencies:
                    return RecordingState.CircularDependency("Circular dependencies in placeholders")
                if not value.is_set:
                    missing_placeholders.add(variable_name)
                if value.missing_dependencies:
                    missing_placeholders.update(value.missing_dependencies)

        available_placeholders = [p.variable_name for p in self.config.placeholders.values()]
        invalid_placeholders = missing_placeholders - set(available_placeholders)

        if invalid_placeholders:
            print(f"Recording {group_id} has invalid placeholders: {invalid_placeholders}")
            return RecordingState.InvalidPlaceholders(invalid_placeholders=list(invalid_placeholders))

        if missing_placeholders:
            print("Recording missing info:", missing_placeholders)
            return RecordingState.MissingInfo(missing_placeholders=list(missing_placeholders))

        print("Recording ready")
        return RecordingState.Ready()

    @thread_bound(timeout_ms=2000)
    def check_recording_state(self, group_id: str):
        recording_state = self.get_recording_state(group_id)
        self.recording_state_changed.emit(group_id, recording_state)

    @thread_bound(timeout_ms=2000)
    def check_all_recording_states(self):
        for group_view in self.config.get_all_group_views():
            self.check_recording_state(group_view.group_id)

    @thread_bound(timeout_ms=2000)
    def refresh_group_view(self, group_id: str):
        group_view = self.config.get_group_view(group_id)
        if not group_view:
            raise ValueError(f"Group view not found for {group_id}")

        self.group_view_changed.emit(group_id, deepcopy(group_view))
        self.check_recording_state(group_id)

    @thread_bound(timeout_ms=2000)
    def refresh_all_group_views(self):
        for group_view in self.config.get_all_group_views():
            self.group_view_changed.emit(group_view.group_id, deepcopy(group_view))
        self.check_all_recording_states()

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
        group_config = self.config.groups.get(camera_config.recording_id)

        conf = {
            "type": "camera",
            "camera_id": camera_config.camera_id,
            "recording_id": camera_config.recording_id,
            "camera_name": camera_config.camera_name,
            "recording_name": group_config.recording_name if group_config else None
        }

        return self.widget_manager.get_widget("camera_"+camera_config.camera_id, conf)

    def remove_camera_widget(self, camera_id: str):
        self.widget_manager.remove_widget("camera_"+camera_id)

    def get_recording_controls_widget(self, recording_config: GroupConfig):
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

            for camera_id in list(self.config.cameras.keys()):
                self.teardown_camera(camera_id)

            self.config = config

            self.reset_non_persistent_variables()

            # Apply changes synchronously, because we need to ensure the cameras are set up before restoring the UI state
            # I guess we could also implement the layout restoration in the widget manager, but this is simpler for now
            for camera_config in self.config.cameras.values():
                self.setup_camera(camera_config.camera_id)

            self.update_model_leases()
            self.setup_recording_controls()

            self.refresh_all_group_views()

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
