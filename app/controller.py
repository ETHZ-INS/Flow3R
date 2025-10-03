import threading
from concurrent.futures import Future
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml
from PySide6.QtCore import QObject, QThread, Signal, QTimer
from rx.disposable import CompositeDisposable
from rx.subject import Subject
from rx import operators as ops

from app.analysis.pose_estimation.composite_pose_model import CompositePoseModel
from app.analysis.pose_estimation.pose_estimation_transform import PoseEstimationTransform
from app.config.camera_config import CameraConfig
from app.config.pipeline_config import PipelineConfig
from app.config.group_config import GroupConfig
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
    camera_name_changed = Signal(str, str)  # camera_id, new_name

    pipeline_added = Signal(PipelineConfig)
    pipeline_removed = Signal(str)  # pipeline_id
    pipeline_updated = Signal(PipelineConfig, PipelineConfig)  # new_pipeline_config, old_pipeline_config

    group_added = Signal(GroupConfig)
    group_removed = Signal(str)  # group_id
    recording_updated = Signal(GroupConfig, GroupConfig)  # new_recording_config, old_recording_config

    placeholder_added = Signal(VariableConfig)
    placeholder_removed = Signal(str)  # variable_name
    placeholder_updated = Signal(VariableConfig, VariableConfig)  # new_variable_config, old_variable_config

    camera_view_changed = Signal(str, CameraConfigView)  # camera_id, new_view
    group_view_changed = Signal(str, GroupConfigView)  # group_id, new_view

    group_assignment_changed = Signal(str, str, str)  # camera_id, new_group_id, old_group_id
    pipeline_assignment_changed = Signal(str, str, str)  # camera_id, new_pipeline_id, old_pipeline_id

    recording_state_changed = Signal(str, RecordingStateBase)  # group_id, state, message
    recording_name_changed = Signal(str, str)  # group_id, new_name

    log_message_added = Signal(str, str)  # message, level

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
    def add_camera(self, camera_config: CameraConfig):
        if self.config.cameras.get(camera_config.camera_id):
            raise ValueError("Camera already exists.")

        self.config.cameras[camera_config.camera_id] = camera_config

        self.setup_camera.future(camera_config.camera_id)
        self.setup_recording_controls.future()
        self.check_recording_state.future(camera_config.camera_id if camera_config.group_id is None else camera_config.group_id)

        QTimer.singleShot(0, lambda: self.camera_added.emit(camera_config))

    @thread_bound(timeout_ms=2000)
    def remove_camera(self, camera_id: str):
        camera_view = self.config.get_camera_view(camera_id)
        if not camera_view:
            raise ValueError("Camera not found.")

        if camera_view.group_id in self.recordings:
            raise RuntimeError("Camera is currently recording.")

        try:
            self.teardown_camera(camera_id)  # Synchronously, because we need to ensure the camera is removed before deleting the config
            if camera_id in self.config.cameras:
                del self.config.cameras[camera_id]
            self.setup_recording_controls()
            self.check_recording_state(camera_view.group_id)
        except Exception as e:
            print(f"Error removing camera: {e}")
            raise

        QTimer.singleShot(0, lambda: self.camera_removed.emit(camera_id))

    @thread_bound(timeout_ms=2000)
    def update_camera(self, camera_config: CameraConfig):
        camera_view = self.config.get_camera_view(camera_config.camera_id)
        if not camera_view:
            raise ValueError("Camera not found.")

        if camera_view.group_id in self.recordings:
            raise RuntimeError("Camera is currently recording.")

        old_config = camera_view.camera

        if camera_config.group_id == "default":
            camera_config.group_id = None

        camera_activated = camera_config.activated and not old_config.activated
        camera_deactivated = not camera_config.activated and old_config.activated

        group_changed = old_config.group_id != camera_config.group_id
        pipeline_changed = old_config.pipeline_id != camera_config.pipeline_id
        name_changed = old_config.camera_name != camera_config.camera_name
        device_config_changed = (old_config.camera_type != camera_config.camera_type or
                                 old_config.active_config != camera_config.active_config)

        if group_changed:
            if camera_config.group_id:
                if camera_config.group_id not in self.config.groups:
                    raise ValueError("Camera group not found.")
                if camera_config.group_id in self.recordings:
                    raise RuntimeError("Camera group is currently recording.")

        if pipeline_changed:
            if camera_config.pipeline_id and camera_config.pipeline_id not in self.config.pipelines:
                raise ValueError("Pipeline not found.")

        self.config.cameras[camera_config.camera_id] = camera_config

        if camera_activated or device_config_changed:
            self.setup_camera.future(camera_config.camera_id)
        elif name_changed or group_changed:
            # TODO: widget should be updated through signals
            self.get_camera_widget(camera_config)

        if camera_deactivated:
            self.teardown_camera.future(camera_config.camera_id)

        if camera_activated or camera_deactivated or group_changed:
            self.setup_recording_controls.future()

        if pipeline_changed:
            self.update_model_leases.future()

        self.check_recording_state.future(camera_config.camera_id if camera_config.group_id is None else camera_config.group_id)

        QTimer.singleShot(0, lambda: self.camera_updated.emit(camera_config, old_config))
        if camera_activated or camera_deactivated:
            QTimer.singleShot(0, lambda: self.camera_activated.emit(camera_config.camera_id, camera_config.activated))
        if group_changed:
            QTimer.singleShot(0, lambda: self.group_assignment_changed.emit(camera_config.camera_id, camera_config.group_id, old_config.group_id))
        if pipeline_changed:
            QTimer.singleShot(0, lambda: self.pipeline_assignment_changed.emit(camera_config.camera_id, camera_config.pipeline_id, old_config.pipeline_id))
        if name_changed:
            QTimer.singleShot(0, lambda: self.camera_name_changed.emit(camera_config.camera_id, camera_config.camera_name))

    @thread_bound(timeout_ms=2000)
    def set_camera_activated(self, camera_id: str, activated: bool):
        camera_config = deepcopy(self.config.cameras.get(camera_id))
        if not camera_config:
            raise ValueError("Camera not found.")
        camera_config.activated = activated
        self.update_camera(camera_config)

    @thread_bound(timeout_ms=2000)
    def assign_camera_to_group(self, camera_id: str, group_id: str):
        camera_config = deepcopy(self.config.cameras.get(camera_id))
        if not camera_config:
            raise ValueError("Camera not found.")
        if group_id is not None and group_id not in self.config.groups:
            raise ValueError("Group not found.")
        camera_config.group_id = group_id if group_id != "default" else None
        self.update_camera(camera_config)

    @thread_bound(timeout_ms=2000)
    def assign_camera_to_pipeline(self, camera_id: str, pipeline_id: str):
        camera_config = self.config.cameras.get(camera_id)
        if not camera_config:
            raise ValueError("Camera not found.")
        if pipeline_id is not None and pipeline_id not in self.config.pipelines:
            raise ValueError("Pipeline not found.")
        camera_config.pipeline_id = pipeline_id
        self.update_camera(camera_config)

    @thread_bound(timeout_ms=2000)
    def add_pipeline(self, pipeline_config: PipelineConfig):
        if self.config.pipelines.get(pipeline_config.pipeline_id):
            raise ValueError("Pipeline already exists.")

        self.config.pipelines[pipeline_config.pipeline_id] = pipeline_config

        QTimer.singleShot(0, lambda: self.pipeline_added.emit(pipeline_config))

    @thread_bound(timeout_ms=2000)
    def remove_pipeline(self, pipeline_id: str):
        if pipeline_id not in self.config.pipelines:
            raise ValueError("Pipeline not found.")

        pipeline_view = self.config.get_pipeline_view(pipeline_id)
        if pipeline_view.pipeline.is_default:
            raise ValueError("Cannot remove default pipeline.")

        if len(pipeline_view.cameras) > 0:
            raise ValueError("Pipeline is in use by cameras, reassign or remove them first.")

        del self.config.pipelines[pipeline_id]

        QTimer.singleShot(0, lambda: self.pipeline_removed.emit(pipeline_id))

    @thread_bound(timeout_ms=2000)
    def update_pipeline(self, pipeline_config: PipelineConfig):
        pipeline_view = self.config.get_pipeline_view(pipeline_config.pipeline_id)
        if not pipeline_view:
            raise ValueError("Pipeline not found.")

        for camera_view in pipeline_view.cameras:
            if camera_view.group_id in self.recordings:
                # TODO: changing the pipeline config should not affect ongoing recordings
                raise RuntimeError("A camera using this pipeline is currently recording.")

        old_pipeline_config = deepcopy(pipeline_view.pipeline)
        self.config.pipelines[pipeline_config.pipeline_id] = pipeline_config

        self.update_model_leases.future()

        for camera_view in pipeline_view.cameras:
            self.check_recording_state.future(camera_view.group_id)

        QTimer.singleShot(0, lambda: self.pipeline_updated.emit(pipeline_config, old_pipeline_config))
        return ConfigChangeResult(success=True, message="Pipeline updated successfully.")

    @thread_bound(timeout_ms=2000)
    def update_model_leases(self):
        pose_models_in_use = set()
        for pipeline_view in self.config.get_all_pipeline_views():
            if len(pipeline_view.cameras) == 0:
                continue
            if not pipeline_view.pipeline.pose_estimation:
                continue
            preset_id = pipeline_view.pipeline.pose_estimation_config.preset_id
            preset = self.config.pose_estimation_presets.get(preset_id)
            if not preset:
                continue
            pose_models_in_use.update(preset.models)

        for pose_model_id, lease in list(self.pose_model_leases.items()):
            if pose_model_id not in pose_models_in_use:
                print(f"Releasing pose model lease for {pose_model_id}")
                lease.dispose()
                del self.pose_model_leases[pose_model_id]

        for pose_model_id in pose_models_in_use:
            if pose_model_id not in self.pose_model_leases:
                print(f"Acquiring pose model lease for {pose_model_id}")
                lease = self.pose_model_manager.acquire_disposable(pose_model_id)
                self.pose_model_leases[pose_model_id] = lease

    @thread_bound(timeout_ms=2000)
    def add_group(self, group_config: GroupConfig):
        if self.config.groups.get(group_config.group_id):
            raise ValueError("Group already exists.")

        self.config.groups[group_config.group_id] = group_config

        self.check_recording_state.future(group_config.group_id)
        QTimer.singleShot(0, lambda: self.group_added.emit(group_config))

    @thread_bound(timeout_ms=2000)
    def remove_group(self, group_id: str):
        if group_id == "default":
            raise ValueError("Cannot remove default group.")

        group_view = self.config.get_group_view(group_id)
        if not group_view:
            raise ValueError("Group not found.")

        if group_id in self.recordings:
            raise RuntimeError("Group is currently recording.")

        if len(group_view.cameras) > 0:
            raise ValueError("There are still cameras assigned to this group.")

        del self.config.groups[group_id]

        QTimer.singleShot(0, lambda: self.group_removed.emit(group_id))

    @thread_bound(timeout_ms=2000)
    def update_group(self, group_config: GroupConfig):
        group_view = self.config.get_group_view(group_config.group_id)
        if not group_view:
            raise ValueError("Group not found.")

        if group_config.group_id == "default":
            # TODO: Save a snapshot of the recording config when starting a recording so the default can be changed while recording
            if any(camera.camera_id in self.recordings for camera in self.config.cameras.values()):
                raise RuntimeError("Cannot modify default group while any camera is recording.")
        else:
            if group_config.group_id in self.recordings:
                raise RuntimeError("Group is currently recording.")

        old_config = deepcopy(group_view.group)
        self.config.groups[group_config.group_id] = group_config

        self.check_recording_state.future(group_config.group_id)

        QTimer.singleShot(0, lambda: self.recording_updated.emit(group_config, old_config))

        if old_config.recording_name != group_config.recording_name:
            QTimer.singleShot(0, lambda: self.recording_name_changed.emit(group_config.group_id, group_config.recording_name))

    @thread_bound(timeout_ms=2000)
    def add_placeholder(self, placeholder_config: VariableConfig):
        if placeholder_config.variable_id in self.config.placeholders:
            raise ValueError("Placeholder already exists.")

        self.config.placeholders[placeholder_config.variable_id] = placeholder_config
        QTimer.singleShot(0, lambda: self.placeholder_added.emit(placeholder_config))
        self.refresh_all_group_views.future()

    @thread_bound(timeout_ms=2000)
    def remove_placeholder(self, variable_id: str):
        if variable_id not in self.config.placeholders:
            raise ValueError("Placeholder not found.")

        del self.config.placeholders[variable_id]
        QTimer.singleShot(0, lambda: self.placeholder_removed.emit(variable_id))
        self.refresh_all_group_views.future()
        self.check_all_recording_states.future()

    @thread_bound(timeout_ms=2000)
    def update_placeholder(self, placeholder_config: VariableConfig):
        old_placeholder_config = self.config.placeholders.get(placeholder_config.variable_id)
        if not old_placeholder_config:
            raise ValueError("Placeholder not found.")

        self.config.placeholders[placeholder_config.variable_id] = placeholder_config

        QTimer.singleShot(0, lambda: self.placeholder_updated.emit(placeholder_config, old_placeholder_config))
        self.refresh_all_group_views.future()
        self.check_all_recording_states.future()

    @thread_bound(timeout_ms=2000)
    def set_variables_project(self, values: dict[str, Any]):
        for variable_id, value in values.items():
            if variable_id not in self.config.values:
                self.config.values[variable_id] = VariableValue(variable_id)
            self.config.values[variable_id].value = value

        self.check_all_recording_states.future()
        self.refresh_all_group_views.future()

    @thread_bound(timeout_ms=2000)
    def set_variables_group(self, group_id: str, values: dict[str, Any]):
        # TODO: Maybe create an actual group per camera that somehow gets its settings from the default group
        group_config = self.config.groups.get(group_id)
        if group_config:
            target_values = group_config.variable_values
        else:
            camera_config = self.config.cameras.get(group_id)
            if not camera_config:
                raise ValueError("Group or Camera not found.")
            target_values = camera_config.variable_values

        for variable_id, value in values.items():
            if variable_id not in target_values:
                target_values[variable_id] = VariableValue(variable_id)
            target_values[variable_id].value = value

        self.check_recording_state.future(group_id)
        self.refresh_group_view.future(group_id)

    @thread_bound(timeout_ms=2000)
    def set_variables_camera(self, camera_id: str, values: dict[str, Any]):
        print(f"Setting camera variables: {values}")
        camera_config = self.config.cameras.get(camera_id)
        if camera_config is None:
            raise ValueError("Camera not found.")

        for variable_id, value in values.items():
            if variable_id not in camera_config.variable_values:
                camera_config.variable_values[variable_id] = VariableValue(variable_id)
            camera_config.variable_values[variable_id].value = value

        camera_view = self.config.get_camera_view(camera_id)

        self.check_recording_state.future(camera_view.group_id)
        self.refresh_group_view.future(camera_view.group_id)

    @thread_bound(timeout_ms=2000)
    def setup_camera(self, camera_id: str):
        camera_view = self.config.get_camera_view(camera_id)
        if not camera_view:
            raise ValueError("Camera not found.")

        if camera_view.group_id in self.recordings:
            raise RuntimeError("Camera is currently recording.")

        if not camera_view.camera.activated:
            return self.teardown_camera(camera_id)

        self.stop_preview(camera_id)

        camera_widget = self.get_camera_widget(camera_view.camera)

        try:
            camera = self.camera_manager.get_camera(camera_id)
            if camera is not None:
                camera.configure(camera_view.camera)
            else:
                camera = self.camera_manager.add_camera(camera_view.camera, remove_if_exists=True)

            self.check_recording_state.future(camera_view.group_id)

            if camera.error:
                camera_widget.set_camera_message("Error: " + camera.error, show_retry=True, show_edit=True)
            else:
                self.start_preview(camera_id)
        except Exception as e:
            import traceback
            print(f"Error setting up camera {camera_id}: {e}")
            traceback.print_exc()

            camera_widget.set_camera_message("Error: " + str(e), show_retry=True, show_edit=True)
            raise

    @thread_bound(timeout_ms=2000)
    def teardown_camera(self, camera_id: str):
        camera_view = self.config.get_camera_view(camera_id)
        if not camera_view:
            raise ValueError("Camera not found.")

        if camera_view.group_id in self.recordings:
            raise RuntimeError("Camera is currently recording.")

        self.stop_preview(camera_id)
        self.camera_manager.remove_camera(camera_id)
        self.remove_camera_widget(camera_id)

    @thread_bound(timeout_ms=5000)
    def camera_error(self, camera_id: str, msg: str):
        self.stop_preview(camera_id)

        camera = self.camera_manager.get_camera(camera_id)
        if camera is not None:
            camera.error = msg

        camera_widget = self.get_camera_widget(camera.camera_config)
        camera_widget.set_camera_message("Error: " + msg, show_retry=True, show_edit=True)

        camera_view = self.config.get_camera_view(camera_id)
        if camera_view:
            self.check_recording_state.future(camera_view.group_id)

    @thread_bound(timeout_ms=2000)
    def setup_recording_controls(self):
        groups_with_controls = set()
        for group_config in self.config.groups.values():
            group_view = self.config.get_group_view(group_config.group_id)
            if len(group_view.cameras) >= 2:
                groups_with_controls.add(group_config.group_id)

        cameras_with_controls = set()
        for camera_config in self.config.cameras.values():
            if not camera_config.activated:
                continue
            if not camera_config.group_id or camera_config.group_id not in groups_with_controls:
                cameras_with_controls.add(camera_config.camera_id)

        for group_id in list(self.groups_with_controls):
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
            raise ValueError("Recording not found.")

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
                preset_id = pipeline_config.pose_estimation_config.preset_id
                preset = self.config.pose_estimation_presets.get(preset_id)
                if not preset:
                    raise ValueError(f"Pose estimation preset {preset_id} not found")

                pose_models = []
                for pose_model_id in preset.models:
                    pose_model_config = self.config.pose_models[pose_model_id]
                    model_lease = self.pose_model_leases.get(pose_model_config.id)
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
                video_file_sink = VideoFileSink(video_file, width=w, height=h, fps=fps, codec='h264')

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

    @thread_bound(timeout_ms=10000)
    def start_recording(self, group_id: str):
        print(f"Starting recording {group_id}")
        if group_id not in self.recordings:
            self.prepare_recording(group_id)

        recording = self.recordings[group_id]
        if recording.started:
            raise RuntimeError("Recording already started.")

        group_view = self.config.get_group_view(group_id)
        if group_view.group.is_default:
            subject = f"camera \"{group_view.cameras[0].camera.camera_name}\""
        else:
            subject = f"group \"{group_view.group.recording_name}\""

        recording.start()
        self.log_message_added.emit(f"Recording started for {subject}", "INFO")
        self.check_recording_state.future(group_id)

    @thread_bound(timeout_ms=2000)
    def stop_recording(self, group_id: str):
        recording = self.recordings.get(group_id)
        if not recording:
            self.check_recording_state.future(group_id)
            return

        if not recording.started or recording.stopped:
            print(f"Recording {group_id} not started or already stopped.")
            del self.recordings[group_id]
        else:
            recording.stop()

        self.check_recording_state.future(group_id)

    @thread_bound(timeout_ms=10000)
    def recording_done(self, group_id: str, result: Future):
        group_view = self.config.get_group_view(group_id)
        if group_view.group.is_default:
            subject = f"camera \"{group_view.cameras[0].camera.camera_name}\""
        else:
            subject = f"group \"{group_view.group.recording_name}\""

        exc = result.exception()
        if exc is None:
            if group_id in self.recordings:
                del self.recordings[group_id]
            self.log_message_added.emit(f"Recording stopped for {subject}", "INFO")
        else:
            recording = self.recordings.get(group_id)
            if recording:
                recording.stop()
                # TODO: I think this could lead to problems
                del self.recordings[group_id]
            self.log_message_added.emit(f"Recording stopped for {subject}: {exc}", "ERROR")

        self.reset_recording_variables.future(group_id)
        self.check_recording_state.future(group_id)

    @thread_bound(timeout_ms=2000)
    def get_recording_state(self, group_id: str):
        if group_id in self.recordings:
            return RecordingState.Running()

        group_view = self.config.get_group_view(group_id)
        if not group_view:
            return RecordingState.Error("Group not found")

        error = group_view.error
        if error:
            return RecordingState.ConfigError(message=error[1], location=error[0])

        cameras = [self.camera_manager.get_camera(cv.camera.camera_id) for cv in group_view.cameras]
        if any(camera is None or not camera.ready for camera in cameras):
            return RecordingState.NotReady("One or more cameras are not ready")

        missing_placeholders = set()

        for camera_view in group_view.cameras:
            required_variables = camera_view.get_required_placeholders()
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
            return RecordingState.InvalidPlaceholders(invalid_placeholders=list(invalid_placeholders))

        if missing_placeholders:
            return RecordingState.MissingInfo(missing_placeholders=list(missing_placeholders))

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
            raise ValueError("Group not found.")

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
        group_config = self.config.groups.get(camera_config.group_id)

        conf = {
            "type": "camera",
            "camera_id": camera_config.camera_id,
            "group_id": camera_config.group_id,
            "camera_name": camera_config.camera_name,
            "recording_name": group_config.recording_name if group_config else None
        }

        return self.widget_manager.get_widget("camera_"+camera_config.camera_id, conf)

    def remove_camera_widget(self, camera_id: str):
        self.widget_manager.remove_widget("camera_"+camera_id)

    def get_recording_controls_widget(self, recording_config: GroupConfig):
        conf = {
            "type": "recording_controls",
            "group_id": recording_config.group_id,
            "recording_name": recording_config.recording_name
        }

        return self.widget_manager.get_widget("recording_controls_"+recording_config.group_id, conf)

    def remove_recording_controls_widget(self, group_id: str):
        self.widget_manager.remove_widget("recording_controls_"+group_id)

    @thread_bound(timeout_ms=10000)
    def load_config(self, config_file: Path):
        if not config_file.exists():
            raise FileNotFoundError("Configuration file not found.")

        if len(self.recordings) > 0:
            raise RuntimeError("Cannot load configuration while recordings are in progress.")

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

        return ui_state

    @thread_bound(timeout_ms=10000)
    def save_config(self, config_file: Path, ui_state: dict = None, su_mode: bool = False):
        if config_file.exists() and not su_mode:
            write_protected = False

            try:
                existing_config_data = yaml.safe_load(config_file.read_text())
                if existing_config_data:
                    write_protected = existing_config_data.get("write_protected", False)
            except yaml.YAMLError:
                pass

            if write_protected:
                raise PermissionError("Configuration file is write-protected and can only be modified in superuser mode.")

        config_data: Dict[str, Any] = {
            "version": "1.0",
            "ui_state": ui_state,
            "config": self.config.to_dict()
        }

        if su_mode:
            config_data["write_protected"] = True

        with open(config_file, 'w+') as f:
            yaml.safe_dump(config_data, f)
