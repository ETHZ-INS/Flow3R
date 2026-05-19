from pathlib import Path
from typing import Optional, Dict

from py3r.media.streaming.operators import observe_on_bounded
from py3r.pose.core.tracking.fixed_instances_tracker import FixedInstancesTracker
from reactivex import operators as ops

import reactivex as rx
from reactivex.disposable import CompositeDisposable
from reactivex.scheduler import EventLoopScheduler

from flow3r.core.api.app.session_context import ISessionContext
from flow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription, PreviewSubscription
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.logger import get_logger

_logger = get_logger(__name__)
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.core.visualization.visualizer_sink import VisualizerSink
from flow3r.plugins.core.node.do_nothing_sink import DoNothingSink
from flow3r.plugins.core.node.video_segment_concatenator import VideoSegmentConcatenator
from flow3r.plugins.core.node.video_segment_reader import VideoSegmentReader
from flow3r.plugins.core.node.video_segment_writer import VideoSegmentWriter
from flow3r.plugins.core.node.video_spool import VideoSpool
from flow3r.plugins.core.node.video_writer_sink import VideoWriterSink
from flow3r.plugins.pose_estimation.node.pose_estimation_transform import PoseEstimationTransform
from flow3r.plugins.pose_estimation.node.pose_filter_transform import PoseFilterTransform
from flow3r.plugins.pose_estimation.node.pose_results_writer import PoseResultsWriterSink
from flow3r.plugins.pose_estimation.node.video_pacer import VideoPacer
from flow3r.plugins.pose_estimation.pipeline.mouse_pose_estimation.config import MousePoseEstimationConfig
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelConfig
from flow3r.plugins.pose_estimation.util.pose_model_service import PoseModelService, PoseModelLease

pose_model_service = PoseModelService()


class MousePoseEstimationPipeline(IPipeline[MousePoseEstimationConfig]):
    def __init__(self):
        self._config: Optional[MousePoseEstimationConfig] = None
        self._widget_handle: Optional[IVisualizerHandle] = None

        self._current_mouse_model_config: Optional[PoseEstimationModelConfig] = None
        self._current_env_model_config: Optional[PoseEstimationModelConfig] = None

        self._mouse_model_lease: Optional[PoseModelLease] = None
        self._env_model_lease: Optional[PoseModelLease] = None

        self._main_scheduler = EventLoopScheduler()
        self._pose_estimation_scheduler = EventLoopScheduler()
        self._writer_scheduler = EventLoopScheduler()

    def configure(self, session_context: ISessionContext, config: MousePoseEstimationConfig, source_names: Dict[str, str]):
        if not self._widget_handle:
            video_source_name = source_names["Video"]
            self._widget_handle = session_context.widget_service.get_visualizer_handle(f"{video_source_name} Pose Preview")

        pose_models_settings = session_context.settings.get(("pose_estimation", "models"))
        assert pose_models_settings is not None
        mouse_pose_model_config = pose_models_settings.models[config.mouse_pose_model_id]
        env_pose_model_config = pose_models_settings.models[config.env_pose_model_id] if config.env_pose_model_id else None

        if not self._config or mouse_pose_model_config != self._current_mouse_model_config:
            if self._mouse_model_lease:
                self._mouse_model_lease.dispose()

            self._mouse_model_lease = pose_model_service.get_model(mouse_pose_model_config)

        if not self._config or env_pose_model_config != self._current_env_model_config:
            if self._env_model_lease:
                self._env_model_lease.dispose()

            self._env_model_lease = pose_model_service.get_model(env_pose_model_config) if env_pose_model_config else None

        self._config = config
        self._current_mouse_model_config = mouse_pose_model_config
        self._current_env_model_config = env_pose_model_config

    def preview(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PreviewSubscription:
        assert self._config is not None
        assert self._current_mouse_model_config is not None
        assert self._current_env_model_config is not None

        source = sources["Video"]

        video_stream = source.pipe(observe_on_bounded(self._main_scheduler, maxsize=16, policy="drop_oldest"), ops.share())

        if self._current_env_model_config is None:
            pose_model_configs = self._current_mouse_model_config
        else:
            pose_model_configs = (self._current_mouse_model_config, self._current_env_model_config)

        pose_estimation_transform = PoseEstimationTransform(pose_model_service, pose_model_configs, batch_size=8)
        pose_input_stream = video_stream.pipe(observe_on_bounded(self._pose_estimation_scheduler, maxsize=16))
        pose_stream = pose_estimation_transform.pipe(pose_input_stream)

        pose_tracker_transform = PoseFilterTransform(FixedInstancesTracker(["mouse_top", "mouse_top", "running_wheel", "smart_home_cage", "home_cage_house", "home_cage_tunnel", "home_cage_climbing_grid", "home_cage_door", "home_cage_waterbottle", "cage_card",]))
        pose_stream = pose_tracker_transform.pipe(pose_stream)

        pose_preview_pacer = VideoPacer(buffer_size=16)
        pose_preview_stream = Stream(
            (video_stream.format, pose_stream.format),
            rx.zip(video_stream.data, pose_stream.data)
        )
        pose_preview_stream = pose_preview_pacer.pipe(pose_preview_stream)

        visualizer_sink = VisualizerSink(session_context.widget_service, f"{source.name} Pose Preview")
        pose_vis_widget_sub = visualizer_sink.subscribe(pose_preview_stream)

        disposable = CompositeDisposable(pose_vis_widget_sub)
        preview_done = pose_vis_widget_sub.done

        return PreviewSubscription(disposable, preview_done)

    def build(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PipelineSubscription:
        assert self._config is not None
        assert self._current_mouse_model_config is not None
        assert self._current_env_model_config is not None

        source = sources["Video"]

        video_stream = Stream(source.format, source.data.pipe(ops.observe_on(self._main_scheduler)))

        video_file = Path(self._config.video_file)
        video_segment_writer = VideoSegmentWriter()
        video_segment_reader = VideoSegmentReader()
        video_segment_concatenator = VideoSegmentConcatenator(video_file)
        video_spool = VideoSpool(video_segment_writer, video_segment_reader, video_segment_concatenator)

        spool_stream = video_spool.pipe(video_stream)
        spool_stream = Stream(spool_stream.format, spool_stream.data.pipe(ops.share()))

        do_nothing_sink = DoNothingSink()

        if self._current_env_model_config is None:
            pose_model_configs = self._current_mouse_model_config
        else:
            pose_model_configs = (self._current_mouse_model_config, self._current_env_model_config)

        pose_estimation_transform = PoseEstimationTransform(pose_model_service, pose_model_configs, batch_size=32)
        pose_preview_pacer = VideoPacer(buffer_size=150)

        vis_video_file = Path(self._config.video_file).with_suffix(".vis.mp4")
        vis_video_writer_sink = VideoWriterSink(vis_video_file)

        pose_results_file = Path(self._config.pose_results_file)
        pose_results_writer = PoseResultsWriterSink(pose_results_file)

        visualizer_sink = VisualizerSink(session_context.widget_service, f"{source.name} Pose Preview")

        pose_input_stream = Stream(source.format, spool_stream.data.pipe(observe_on_bounded(self._pose_estimation_scheduler)))
        pose_stream = pose_estimation_transform.pipe(pose_input_stream)
        pose_stream = Stream(pose_stream.format, pose_stream.data.pipe(ops.observe_on(self._main_scheduler), ops.share()))

        pose_render_input_stream = Stream((spool_stream.format, pose_stream.format), rx.zip(spool_stream.data, pose_stream.data))

        #pose_vis_stream = pose_render_transform.pipe(pose_render_input_stream)
        #pose_vis_stream = Stream(pose_vis_stream.format, pose_vis_stream.observable.pipe(ops.share()))

        #vis_video_writer_stream = Stream(source.format, pose_vis_stream.observable.pipe(ops.observe_on(self._writer_scheduler)))
        pose_results_writer_stream = Stream(source.format, pose_stream.data.pipe(ops.observe_on(self._writer_scheduler)))
        pose_preview_stream = pose_preview_pacer.pipe(pose_render_input_stream)

        video_writer_sub = do_nothing_sink.subscribe(spool_stream)
        #vis_video_writer_sub = vis_video_writer_sink.subscribe(vis_video_writer_stream)
        pose_results_writer_sub = pose_results_writer.subscribe(pose_results_writer_stream)
        pose_vis_widget_sub = visualizer_sink.subscribe(pose_preview_stream)

        disposable = CompositeDisposable(video_writer_sub, pose_results_writer_sub)
        primary_done = video_writer_sub.done
        secondary_done = rx.zip(pose_results_writer_sub.done)

        return PipelineSubscription(disposable, primary_done, secondary_done)

    def dispose(self):
        if self._mouse_model_lease:
            self._mouse_model_lease.dispose()
            self._mouse_model_lease = None

        if self._env_model_lease:
            self._env_model_lease.dispose()
            self._env_model_lease = None

        if self._widget_handle:
            self._widget_handle.dispose()
            self._widget_handle = None
