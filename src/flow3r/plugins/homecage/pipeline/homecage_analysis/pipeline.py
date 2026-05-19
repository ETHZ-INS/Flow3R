import uuid
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from py3r.media.streaming.operators import observe_on_bounded
from py3r.media.types import VideoFrame
from py3r.media.video.ffmpeg_video_file_writer import FFmpegVideoFileWriter
from py3r.pose.core.tracking.fixed_instances_tracker import FixedInstancesTracker
from reactivex import operators as ops, Observable

import reactivex as rx
from reactivex.disposable import CompositeDisposable
from reactivex.scheduler import EventLoopScheduler

from flow3r.core.api.app.session_context import ISessionContext
from flow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription, PreviewSubscription, PipelineBase
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from flow3r.core.visualization.visualizer_sink import VisualizerSink
from flow3r.logger import get_logger

_logger = get_logger(__name__)
from flow3r.plugins.core.node.do_nothing_sink import DoNothingSink
from flow3r.plugins.core.node.video_segment_concatenator import VideoSegmentConcatenator
from flow3r.plugins.core.node.video_segment_reader import VideoSegmentReader
from flow3r.plugins.core.node.video_segment_writer import VideoSegmentWriter
from flow3r.plugins.core.typing.video import VideoFormat
from flow3r.plugins.homecage.node.live_results_sink import HomecageLiveResultsSink
from flow3r.plugins.homecage.node.pose_segment_writer_transform import PoseSegmentWriter
from flow3r.plugins.homecage.pipeline.homecage_analysis.config import HomecageAnalysisConfig
from flow3r.plugins.homecage.typing.data_segment import HomecageDataSegmentFormat, HomecageDataSegment, TopDataSegment, \
    TopCameraDataSegment
from flow3r.plugins.pose_estimation.node.pose_estimation_transform import PoseEstimationTransform
from flow3r.plugins.pose_estimation.node.pose_filter_transform import PoseFilterTransform
from flow3r.plugins.pose_estimation.node.pose_results_writer import PoseResultsWriterSink
from flow3r.plugins.pose_estimation.node.video_pacer import VideoPacer
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelConfig
from flow3r.plugins.pose_estimation.util.pose_model_service import PoseModelService, PoseModelLease

pose_model_service = PoseModelService()

_main_scheduler = EventLoopScheduler()
_pose_estimation_scheduler = EventLoopScheduler()
_video_writer_scheduler = EventLoopScheduler()
_video_reader_scheduler = EventLoopScheduler()
_writer_scheduler = EventLoopScheduler()


def sync_by_timestamp(cam_a, cam_b, tol: float):
    """
    cam_a, cam_b: Observable[VideoFrame]
    tol: allowed timestamp difference (same units as VideoFrame.ts)
    returns: Observable[Tuple[VideoFrame, VideoFrame]]
    """

    def try_match(a_q: List[VideoFrame], b_q: List[VideoFrame]) -> Tuple[List[Tuple[VideoFrame, VideoFrame]], List[VideoFrame], List[VideoFrame]]:
        out = []

        # Keep trying while both sides have frames
        while a_q and b_q:
            a = a_q[0]
            b = b_q[0]
            dt = a.timestamp - b.timestamp

            if abs(dt) <= tol:
                # Matched!
                out.append((a, b))
                a_q.pop(0)
                b_q.pop(0)
            elif dt < -tol:
                # a is too early (older). Drop/advance a.
                _logger.debug("sync_by_timestamp - Dropping frame from A")
                a_q.pop(0)
            else:
                # b is too early (older). Drop/advance b.
                _logger.debug("sync_by_timestamp - Dropping frame from B")
                b_q.pop(0)

        return out, a_q, b_q

    # Tag frames by source, merge into one stream, and keep state
    tagged = rx.merge(
        cam_a.pipe(ops.map(lambda f: ("a", f))),
        cam_b.pipe(ops.map(lambda f: ("b", f))),
    )

    def accumulator(state, item):
        a_q, b_q = state
        side, frame = item
        if side == "a":
            a_q.append(frame)
        else:
            b_q.append(frame)

        matched, a_q, b_q = try_match(a_q, b_q)
        return a_q, b_q, matched

    return tagged.pipe(
        ops.scan(lambda s, item: accumulator((s[0], s[1]), item), seed=([], [], [])),
        ops.flat_map(lambda s: rx.from_iterable(s[2])),  # emit all matched pairs
    )


def video_writer_factory(segment_file: Path, desc: VideoFormat):
    return FFmpegVideoFileWriter(segment_file, desc.size, desc.fps, grayscale=desc.fmt=="mono8", quality="low")


class HomecageAnalysisPipeline(PipelineBase[HomecageAnalysisConfig]):
    def __init__(self):
        self._config: Optional[HomecageAnalysisConfig] = None

        self._current_mouse_model_config: Optional[PoseEstimationModelConfig] = None
        self._current_env_model_config: Optional[PoseEstimationModelConfig] = None

        self._top_preview_widget_handle: Optional[IVisualizerHandle] = None
        self._offset_preview_widget_handle: Optional[IVisualizerHandle] = None

        self._mouse_model_lease: Optional[PoseModelLease] = None
        self._env_model_lease: Optional[PoseModelLease] = None

    def _configure_widget_handles(self, session_context: ISessionContext, config: HomecageAnalysisConfig):
        if not self._top_preview_widget_handle:
            self._top_preview_widget_handle = session_context.widget_service.get_visualizer_handle("Top Preview")

        if not self._offset_preview_widget_handle:
            self._offset_preview_widget_handle = session_context.widget_service.get_visualizer_handle("Offset Preview")

    def _dispose_widget_handles(self):
        if self._top_preview_widget_handle:
            self._top_preview_widget_handle.dispose()
            self._top_preview_widget_handle = None

        if self._offset_preview_widget_handle:
            self._offset_preview_widget_handle.dispose()
            self._offset_preview_widget_handle = None

    def _configure_pose_models(self, session_context: ISessionContext, config: HomecageAnalysisConfig):
        pose_models_settings = session_context.settings.get(("pose_estimation", "models"))
        if not pose_models_settings:
            self._dispose_pose_models()
            return

        mouse_pose_model_config = pose_models_settings.models.get(config.mouse_pose_model_id)
        env_pose_model_config = pose_models_settings.models.get(config.environment_pose_model_id)

        if mouse_pose_model_config:
            if mouse_pose_model_config != self._current_mouse_model_config:
                if self._mouse_model_lease:
                    self._mouse_model_lease.dispose()
                    self._mouse_model_lease = None
                self._mouse_model_lease = pose_model_service.get_model(mouse_pose_model_config)
                self._current_mouse_model_config = mouse_pose_model_config
        else:
            if self._mouse_model_lease:
                self._mouse_model_lease.dispose()
                self._mouse_model_lease = None

        if env_pose_model_config:
            if env_pose_model_config != self._current_env_model_config:
                if self._env_model_lease:
                    self._env_model_lease.dispose()
                    self._env_model_lease = None
                self._env_model_lease = pose_model_service.get_model(env_pose_model_config)
                self._current_env_model_config = env_pose_model_config
        else:
            if self._env_model_lease:
                self._env_model_lease.dispose()
                self._env_model_lease = None

    def _dispose_pose_models(self):
        if self._mouse_model_lease:
            self._mouse_model_lease.dispose()
            self._mouse_model_lease = None

        if self._env_model_lease:
            self._env_model_lease.dispose()
            self._env_model_lease = None

    def configure(self, session_context: ISessionContext, config: HomecageAnalysisConfig):
        self._configure_widget_handles(session_context, config)
        self._configure_pose_models(session_context, config)

        self._config = config

    def _split_3d_video(self, source: IStream[VideoFormat, VideoFrame]) -> Tuple[Stream[VideoFormat, VideoFrame], Stream[VideoFormat, VideoFrame]]:
        source = source.pipe(ops.share())
        width, height = source.format.size
        new_format = VideoFormat((width // 2, height), source.format.fps, source.format.fmt)

        return Stream(
            new_format,
            source.data.pipe(ops.map(lambda f: f.with_image(f.img[:, :f.img.shape[1] // 2])))
        ), Stream(
            new_format,
            source.data.pipe(ops.map(lambda f: f.with_image(f.img[:, f.img.shape[1] // 2:])))
        )

    def preview(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PreviewSubscription:
        assert self._config is not None
        assert self._current_mouse_model_config is not None
        assert self._current_env_model_config is not None

        if self._config.use_3d_camera:
            camera_source = sources["Top 3D Video"]
            top_camera_synced, offset_camera_synced = self._split_3d_video(camera_source)
        else:
            top_camera_source = sources["Top Video"]
            offset_camera_source = sources["Offset Video"]

            paired: Observable[tuple[VideoFrame, VideoFrame]] = sync_by_timestamp(top_camera_source.data, offset_camera_source.data, tol=1 / 60)
            paired_shared = paired.pipe(ops.share())

            top_camera_synced = Stream(top_camera_source.format, paired_shared.pipe(ops.map(lambda t: t[0])))
            offset_camera_synced = Stream(offset_camera_source.format, paired_shared.pipe(ops.map(lambda t: t[1])))

        pose_model_configs = (self._current_mouse_model_config, self._current_env_model_config)
        top_pose_estimation_transform = PoseEstimationTransform(pose_model_service, pose_model_configs, batch_size=8)
        offset_pose_estimation_transform = PoseEstimationTransform(pose_model_service, pose_model_configs, batch_size=8)

        top_camera_synced = top_camera_synced.pipe(ops.observe_on(_main_scheduler), ops.share())
        offset_camera_synced = offset_camera_synced.pipe(ops.observe_on(_main_scheduler), ops.share())

        top_pose_input_stream = top_camera_synced.pipe(observe_on_bounded(_pose_estimation_scheduler))
        offset_pose_input_stream = offset_camera_synced.pipe(observe_on_bounded(_pose_estimation_scheduler))

        top_pose_stream = top_pose_estimation_transform.pipe(top_pose_input_stream).pipe(ops.observe_on(_main_scheduler), ops.share())
        offset_pose_stream = offset_pose_estimation_transform.pipe(offset_pose_input_stream).pipe(ops.observe_on(_main_scheduler), ops.share())

        pose_tracker_transform = PoseFilterTransform(FixedInstancesTracker(
            ["mouse_top", "mouse_top", "mouse_top", "mouse_top", "running_wheel", "smart_home_cage", "home_cage_house", "home_cage_tunnel",
             "home_cage_climbing_grid", "home_cage_door", "home_cage_waterbottle", "cage_card", ]))

        top_pose_stream = pose_tracker_transform.pipe(top_pose_stream)
        offset_pose_stream = pose_tracker_transform.pipe(offset_pose_stream)

        top_pose_preview_pacer = VideoPacer(buffer_size=16)
        top_pose_preview_stream = Stream(
            (top_camera_synced.format, top_pose_stream.format),
            rx.zip(top_camera_synced.data, top_pose_stream.data)
        )
        top_pose_preview_stream = top_pose_preview_pacer.pipe(top_pose_preview_stream)

        offset_pose_preview_pacer = VideoPacer(buffer_size=16)
        offset_pose_preview_stream = Stream(
            (offset_camera_synced.format, offset_pose_stream.format),
            rx.zip(offset_camera_synced.data, offset_pose_stream.data)
        )
        offset_pose_preview_stream = offset_pose_preview_pacer.pipe(offset_pose_preview_stream)

        top_visualizer_sink = VisualizerSink(session_context.widget_service, "Top Preview")
        top_pose_vis_widget_sub = top_visualizer_sink.subscribe(top_pose_preview_stream)
        #top_pose_vis_widget_sub = DoNothingSink().subscribe(top_pose_preview_stream)

        offset_visualizer_sink = VisualizerSink(session_context.widget_service, "Offset Preview")
        offset_pose_vis_widget_sub = offset_visualizer_sink.subscribe(offset_pose_preview_stream)
        #offset_pose_vis_widget_sub = DoNothingSink().subscribe(offset_pose_preview_stream)

        disposable = CompositeDisposable(top_pose_vis_widget_sub, offset_pose_vis_widget_sub)
        preview_done = rx.zip(top_pose_vis_widget_sub.done, offset_pose_vis_widget_sub.done)
        return PreviewSubscription(disposable, preview_done)

    def build(self, session_context: ISessionContext, sources: Dict[str, IStream]) -> PipelineSubscription:
        assert self._config is not None
        assert self._current_mouse_model_config is not None
        assert self._current_env_model_config is not None

        if self._config.use_3d_camera:
            camera_source = sources["Top 3D Video"]
            top_camera_synced, offset_camera_synced = self._split_3d_video(camera_source)
        else:
            top_camera_source = sources["Top Video"]
            offset_camera_source = sources["Offset Video"]

            paired: Observable[tuple[VideoFrame, VideoFrame]] = sync_by_timestamp(top_camera_source.data, offset_camera_source.data, tol=1 / 60)
            paired_shared = paired.pipe(ops.share())

            top_camera_synced = Stream(top_camera_source.format, paired_shared.pipe(ops.map(lambda t: t[0])))
            offset_camera_synced = Stream(offset_camera_source.format, paired_shared.pipe(ops.map(lambda t: t[1])))

        top_video_segment_writer = VideoSegmentWriter(writer_factory=video_writer_factory, segment_length_seconds=5.0)
        offset_video_segment_writer = VideoSegmentWriter(writer_factory=video_writer_factory, segment_length_seconds=5.0)

        top_camera_synced = top_camera_synced.pipe(ops.observe_on(_video_writer_scheduler), ops.share())
        offset_camera_synced = offset_camera_synced.pipe(ops.observe_on(_video_writer_scheduler), ops.share())

        top_video_segment_stream = top_video_segment_writer.pipe(top_camera_synced).pipe(ops.observe_on(_main_scheduler), ops.share())
        offset_video_segment_stream = offset_video_segment_writer.pipe(offset_camera_synced).pipe(ops.observe_on(_main_scheduler), ops.share())

        top_video_segment_reader = VideoSegmentReader()
        offset_video_segment_reader = VideoSegmentReader()

        top_spool_stream = top_video_segment_reader.pipe(top_video_segment_stream.pipe(ops.observe_on(_video_reader_scheduler)))
        offset_spool_stream = offset_video_segment_reader.pipe(offset_video_segment_stream.pipe(ops.observe_on(_video_reader_scheduler)))

        top_video_segment_concatenator = VideoSegmentConcatenator(Path(self._config.top_video_file))
        offset_video_segment_concatenator = VideoSegmentConcatenator(Path(self._config.offset_video_file))

        top_video_sub = top_video_segment_concatenator.subscribe(top_video_segment_stream)
        offset_video_sub = offset_video_segment_concatenator.subscribe(offset_video_segment_stream)

        pose_model_configs = (self._current_mouse_model_config, self._current_env_model_config)
        top_pose_estimation_transform = PoseEstimationTransform(pose_model_service, pose_model_configs, batch_size=30)
        offset_pose_estimation_transform = PoseEstimationTransform(pose_model_service, pose_model_configs, batch_size=30)

        top_pose_input_stream = top_spool_stream.pipe(observe_on_bounded(_pose_estimation_scheduler))
        offset_pose_input_stream = offset_spool_stream.pipe(observe_on_bounded(_pose_estimation_scheduler))

        top_pose_stream = top_pose_estimation_transform.pipe(top_pose_input_stream)
        offset_pose_stream = offset_pose_estimation_transform.pipe(offset_pose_input_stream)

        pose_tracker_transform = PoseFilterTransform(FixedInstancesTracker(
            ["mouse_top", "mouse_top", "mouse_top", "mouse_top", "running_wheel", "smart_home_cage", "home_cage_house", "home_cage_tunnel",
             "home_cage_climbing_grid", "home_cage_door", "home_cage_waterbottle", "cage_card"]))

        top_pose_stream = pose_tracker_transform.pipe(top_pose_stream)
        offset_pose_stream = pose_tracker_transform.pipe(offset_pose_stream)

        top_pose_stream = top_pose_stream.pipe(observe_on_bounded(_writer_scheduler), ops.share())
        offset_pose_stream = offset_pose_stream.pipe(observe_on_bounded(_writer_scheduler), ops.share())

        #top_pose_results_file = Path(self._config.top_pose_results_file)
        #top_pose_results_writer = PoseResultsWriterSink(top_pose_results_file)
        #offset_pose_results_file = Path(self._config.offset_pose_results_file)
        #offset_pose_results_writer = PoseResultsWriterSink(offset_pose_results_file)

        calibration_file = Path(self._config.calibration_file)

        top_pose_segment_writer = PoseSegmentWriter(segment_length_seconds=5.0)
        offset_pose_segment_writer = PoseSegmentWriter(segment_length_seconds=5.0)

        top_pose_results_writer_stream = Stream(
            (top_spool_stream.format, top_pose_stream.format),
            top_pose_stream.data
        )
        offset_pose_results_writer_stream = Stream(
            (offset_spool_stream.format, offset_pose_stream.format),
            offset_pose_stream.data
        )

        top_pose_segment_stream = top_pose_segment_writer.pipe(top_pose_results_writer_stream).pipe(ops.observe_on(_main_scheduler), ops.share())
        offset_pose_segment_stream = offset_pose_segment_writer.pipe(offset_pose_results_writer_stream).pipe(ops.observe_on(_main_scheduler), ops.share())

        top_pose_sink = DoNothingSink()
        offset_pose_sink = DoNothingSink()

        top_pose_results_sub = top_pose_sink.subscribe(top_pose_segment_stream)
        offset_pose_results_sub = offset_pose_sink.subscribe(offset_pose_segment_stream)

        data_format = HomecageDataSegmentFormat(top_video_segment_stream.format, top_pose_segment_stream.format, 5.0)

        def _build_data_segment(segments):
            top_video_segment, offset_video_segment, top_pose_segment, offset_pose_segment = segments
            assert top_video_segment.segment_index == offset_video_segment.segment_index == top_pose_segment.segment_index == offset_pose_segment.segment_index
            return HomecageDataSegment(
                top_video_segment.segment_index,
                TopDataSegment(
                    TopCameraDataSegment(top_video_segment.file_path, None, top_pose_segment.file_path),
                    TopCameraDataSegment(offset_video_segment.file_path, None, offset_pose_segment.file_path),
                    calibration_file
                )
            )

        data_observable = rx.zip(
            top_video_segment_stream.data,
            offset_video_segment_stream.data,
            top_pose_segment_stream.data,
            offset_pose_segment_stream.data
        ).pipe(
            ops.map(_build_data_segment),
            ops.do_action(print)
        )
        data_segment_stream = Stream(data_format, data_observable)

        live_results_input_folder = Path(self._config.live_results_input_folder)
        recording_id = str(uuid.uuid4())
        def segment_folder_factory(segment_index: int) -> Path:
            folder = live_results_input_folder / f"{recording_id}_segment_{segment_index}"
            return folder

        data_segment_sink = HomecageLiveResultsSink(segment_folder_factory)
        data_segment_sub = data_segment_sink.subscribe(data_segment_stream)

        top_pose_preview_pacer = VideoPacer(buffer_size=16)
        top_pose_preview_stream = Stream(
            (top_camera_synced.format, top_pose_stream.format),
            rx.zip(top_camera_synced.data, top_pose_stream.data)
        )
        top_pose_preview_stream = top_pose_preview_pacer.pipe(top_pose_preview_stream)

        offset_pose_preview_pacer = VideoPacer(buffer_size=16)
        offset_pose_preview_stream = Stream(
            (offset_camera_synced.format, offset_pose_stream.format),
            rx.zip(offset_camera_synced.data, offset_pose_stream.data)
        )
        offset_pose_preview_stream = offset_pose_preview_pacer.pipe(offset_pose_preview_stream)

        top_visualizer_sink = VisualizerSink(session_context.widget_service, "Top Preview")
        #top_pose_vis_widget_sub = top_visualizer_sink.subscribe(top_pose_preview_stream)

        offset_visualizer_sink = VisualizerSink(session_context.widget_service, "Offset Preview")
        #offset_pose_vis_widget_sub = offset_visualizer_sink.subscribe(offset_pose_preview_stream)

        disposable = CompositeDisposable(top_video_sub, offset_video_sub, top_pose_results_sub, offset_pose_results_sub, data_segment_sub)#, top_pose_vis_widget_sub, offset_pose_vis_widget_sub)
        primary_done = rx.zip(top_video_sub.done, offset_video_sub.done)
        secondary_done = rx.zip(top_pose_results_sub.done, offset_pose_results_sub.done, data_segment_sub.done)

        return PipelineSubscription(disposable, primary_done, secondary_done)

    def dispose(self):
        self._dispose_widget_handles()
        self._dispose_pose_models()
