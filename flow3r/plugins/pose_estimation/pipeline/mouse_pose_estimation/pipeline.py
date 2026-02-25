from pathlib import Path
from typing import List, Optional

from reactivex import operators as ops

import reactivex as rx
from reactivex.disposable import CompositeDisposable
from reactivex.scheduler import EventLoopScheduler

from flow3r.core.api.app.session_context import ISessionContext
from flow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.core.visualization.visualizer_sink import VisualizerSink
from flow3r.plugins.core.node.do_nothing_sink import DoNothingSink
from flow3r.plugins.core.node.video_segment_concatenator import VideoSegmentConcatenator
from flow3r.plugins.core.node.video_segment_reader import VideoSegmentReader
from flow3r.plugins.core.node.video_segment_writer import VideoSegmentWriter
from flow3r.plugins.core.node.video_spool import VideoSpool
from flow3r.plugins.core.node.video_writer_sink import VideoWriterSink
from flow3r.plugins.pose_estimation.node.pose_estimation_transform import PoseEstimationTransform
from flow3r.plugins.pose_estimation.node.pose_render_transform import PoseRenderTransform
from flow3r.plugins.pose_estimation.node.pose_results_writer import PoseResultsWriterSink
from flow3r.plugins.pose_estimation.node.video_pacer import VideoPacer
from flow3r.plugins.pose_estimation.pipeline.pose_estimation.config import PoseEstimationConfig
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelConfig
from flow3r.plugins.pose_estimation.util.pose_model_service import PoseModelService, PoseModelLease

pose_model_service = PoseModelService()


_main_scheduler = EventLoopScheduler()
_pose_estimation_scheduler = EventLoopScheduler()
_writer_scheduler = EventLoopScheduler()


class PoseEstimationPipeline(IPipeline[PoseEstimationConfig]):
    def __init__(self):
        self._config: Optional[PoseEstimationConfig] = None
        self._widget_handle: Optional[IVisualizerHandle] = None

        self._current_model_config: Optional[PoseEstimationModelConfig] = None
        self._model_lease: Optional[PoseModelLease] = None

    def configure(self, session_context: ISessionContext, config: PoseEstimationConfig):
        print("PoseEstimationPipeline.configure", config)
        if not self._widget_handle:
            self._widget_handle = session_context.widget_service.get_visualizer_handle("Pose Preview")

        pose_models_settings = session_context.settings.get(("pose_estimation", "models"))
        assert pose_models_settings is not None
        pose_model_config = pose_models_settings.models[config.pose_model_id]

        if not self._config or pose_model_config != self._current_model_config:
            if self._model_lease:
                self._model_lease.dispose()

            self._model_lease = pose_model_service.get_model(pose_model_config)

        self._config = config
        self._current_model_config = pose_model_config

    def build(self, session_context: ISessionContext, sources: List[IStream]) -> PipelineSubscription:
        assert len(sources) == 1
        source = sources[0]

        video_stream = Stream(source.descriptor, source.observable.pipe(ops.observe_on(_main_scheduler)))

        video_file = Path(self._config.video_file)
        video_segment_writer = VideoSegmentWriter()
        video_segment_reader = VideoSegmentReader()
        video_segment_concatenator = VideoSegmentConcatenator(video_file)
        video_spool = VideoSpool(video_segment_writer, video_segment_reader, video_segment_concatenator)

        spool_stream = video_spool.pipe(video_stream)
        spool_stream = Stream(spool_stream.descriptor, spool_stream.observable.pipe(ops.share()))

        do_nothing_sink = DoNothingSink()

        pose_estimation_transform = PoseEstimationTransform(pose_model_service, self._current_model_config, batch_size=32)
        pose_render_transform = PoseRenderTransform()
        pose_preview_pacer = VideoPacer(buffer_size=150)

        vis_video_file = Path(self._config.video_file).with_suffix(".vis.mp4")
        vis_video_writer_sink = VideoWriterSink(vis_video_file)

        pose_results_file = Path(self._config.pose_results_file)
        pose_results_writer = PoseResultsWriterSink(pose_results_file)

        visualizer_sink = VisualizerSink(session_context.widget_service, "Pose Preview")

        pose_input_stream = Stream(source.descriptor, spool_stream.observable.pipe(ops.observe_on(_pose_estimation_scheduler)))
        pose_stream = pose_estimation_transform.pipe(pose_input_stream)
        pose_stream = Stream(pose_stream.descriptor, pose_stream.observable.pipe(ops.observe_on(_main_scheduler), ops.share()))

        pose_render_input_stream = Stream(rx.combine_latest(spool_stream.descriptor, pose_stream.descriptor), rx.zip(spool_stream.observable, pose_stream.observable))

        #pose_vis_stream = pose_render_transform.pipe(pose_render_input_stream)
        #pose_vis_stream = Stream(pose_vis_stream.descriptor, pose_vis_stream.observable.pipe(ops.share()))

        #vis_video_writer_stream = Stream(source.descriptor, pose_vis_stream.observable.pipe(ops.observe_on(_writer_scheduler)))
        pose_results_writer_stream = Stream(source.descriptor, pose_stream.observable.pipe(ops.observe_on(_writer_scheduler)))
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
        if self._model_lease:
            self._model_lease.dispose()
            self._model_lease = None

        if self._widget_handle:
            self._widget_handle.dispose()
            self._widget_handle = None
