import uuid
from pathlib import Path
from typing import List, Optional

from py3r.media.streaming.operators import observe_on_bounded
from py3r.media.video.ffmpeg_video_file_writer import FFmpegVideoFileWriter
from reactivex import operators as ops

import reactivex as rx
from reactivex.disposable import CompositeDisposable
from reactivex.scheduler import EventLoopScheduler

from flow3r.core.api.app.session_context import ISessionContext
from flow3r.core.pipeline.abc.pipeline import IPipeline, PipelineSubscription
from flow3r.core.streaming.abc.stream import IStream
from flow3r.core.streaming.stream import Stream
from flow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
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
from flow3r.plugins.pose_estimation.settings.pose_estimation_models.settings import PoseEstimationModelConfig
from flow3r.plugins.pose_estimation.util.pose_model_service import PoseModelService, PoseModelLease

pose_model_service = PoseModelService()

_main_scheduler = EventLoopScheduler()
_pose_estimation_scheduler = EventLoopScheduler()
_video_writer_scheduler = EventLoopScheduler()
_video_reader_scheduler = EventLoopScheduler()
_writer_scheduler = EventLoopScheduler()


def video_writer_factory(segment_file: Path, desc: VideoFormat):
    segment_file.parent.mkdir(parents=True, exist_ok=True)
    return FFmpegVideoFileWriter(segment_file, desc.size, desc.fps, grayscale=desc.fmt=="mono8", quality="medium")


class HomecageAnalysisPipeline(IPipeline[HomecageAnalysisConfig]):
    def __init__(self):
        self._config: Optional[HomecageAnalysisConfig] = None
        self._widget_handle: Optional[IVisualizerHandle] = None

        self._current_mouse_model_config: Optional[PoseEstimationModelConfig] = None
        self._current_env_model_config: Optional[PoseEstimationModelConfig] = None
        self._mouse_model_lease: Optional[PoseModelLease] = None
        self._env_model_lease: Optional[PoseModelLease] = None

    def configure(self, session_context: ISessionContext, config: HomecageAnalysisConfig):
        pose_models_settings = session_context.settings.get(("pose_estimation", "models"))
        assert pose_models_settings is not None

        mouse_pose_model_config = pose_models_settings.models[config.mouse_pose_model_id]
        env_pose_model_config = pose_models_settings.models[config.environment_pose_model_id]

        if not self._config or mouse_pose_model_config != self._current_mouse_model_config:
            if self._mouse_model_lease:
                self._mouse_model_lease.dispose()

            self._mouse_model_lease = pose_model_service.get_model(mouse_pose_model_config)

        if not self._config or env_pose_model_config != self._current_env_model_config:
            if self._env_model_lease:
                self._env_model_lease.dispose()

            self._env_model_lease = pose_model_service.get_model(env_pose_model_config)

        self._config = config
        self._current_mouse_model_config = mouse_pose_model_config
        self._current_env_model_config = env_pose_model_config

    def build(self, session_context: ISessionContext, sources: List[IStream]) -> PipelineSubscription:
        assert len(sources) == 2
        assert self._config is not None
        assert self._current_mouse_model_config is not None
        assert self._current_env_model_config is not None

        top_camera_source = sources[0]
        offset_camera_source = sources[1]

#        top_camera_source = Stream(
#            top_camera_source.descriptor.pipe(ops.map(lambda d: VideoFormat((int(d.size[0]/2), int(d.size[1]/2)), d.fps, d.fmt))),
#            top_camera_source.observable.pipe(ops.map(lambda f: f.with_image(cv2.resize(f.img, (int(1920/2), int(1080/2)), interpolation=cv2.INTER_AREA))))
#        )
#
#        offset_camera_source = Stream(
#            offset_camera_source.descriptor.pipe(ops.map(lambda d: VideoFormat((int(d.size[0]/2), int(d.size[1]/2)), d.fps, d.fmt))),
#            offset_camera_source.observable.pipe(ops.map(lambda f: f.with_image(cv2.resize(f.img, (int(1920/2), int(1080/2)), interpolation=cv2.INTER_AREA))))
#        )

#        top_video_writer_sink = VideoWriterSink(Path(self._config.top_video_file))
#        offset_video_writer_sink = VideoWriterSink(Path(self._config.offset_video_file))
#
#        top_video_sub = top_video_writer_sink.subscribe(top_camera_source)
#        offset_video_sub = offset_video_writer_sink.subscribe(offset_camera_source)
#
#        primary_done = rx.zip(top_video_sub.done, offset_video_sub.done)
#        secondary_done = None
#
#        return PipelineSubscription(CompositeDisposable(top_video_sub, offset_video_sub), primary_done, secondary_done)
        
#        def build_spool_stream(source: IStream, video_file: Path) -> IStream:
#            video_stream = Stream(source.descriptor, source.observable.pipe(ops.observe_on(_video_writer_scheduler)))
#
#            video_segment_writer = VideoSegmentWriter()
#            video_segment_reader = VideoSegmentReader()
#            video_segment_concatenator = VideoSegmentConcatenator(video_file)
#            video_spool = VideoSpool(video_segment_writer, video_segment_reader, video_segment_concatenator)
#
#            spool_stream = video_spool.pipe(video_stream)
#            spool_stream = Stream(spool_stream.descriptor, spool_stream.observable.pipe(ops.observe_on(_main_scheduler), ops.share()))
#            return spool_stream
#
#        top_spool_stream = build_spool_stream(top_camera_source, Path(self._config.top_video_file))
#        offset_spool_stream = build_spool_stream(offset_camera_source, Path(self._config.offset_video_file))
#
#        top_spool_sink = DoNothingSink()
#        offset_spool_sink = DoNothingSink()
#
#        top_spool_sub = top_spool_sink.subscribe(top_spool_stream)
#        offset_spool_sub = offset_spool_sink.subscribe(offset_spool_stream)

        top_video_segment_writer = VideoSegmentWriter(writer_factory=video_writer_factory, segment_length_seconds=5.0)
        offset_video_segment_writer = VideoSegmentWriter(writer_factory=video_writer_factory, segment_length_seconds=5.0)

        top_camera_source = top_camera_source.pipe(ops.observe_on(_video_writer_scheduler))
        offset_camera_source = offset_camera_source.pipe(ops.observe_on(_video_writer_scheduler))

        top_video_segment_stream = top_video_segment_writer.pipe(top_camera_source).pipe(ops.observe_on(_main_scheduler), ops.share())
        offset_video_segment_stream = offset_video_segment_writer.pipe(offset_camera_source).pipe(ops.observe_on(_main_scheduler), ops.share())

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
        top_pose_stream = top_pose_stream.pipe(observe_on_bounded(_writer_scheduler), ops.share())
        offset_pose_stream = offset_pose_estimation_transform.pipe(offset_pose_input_stream)
        offset_pose_stream = offset_pose_stream.pipe(observe_on_bounded(_writer_scheduler), ops.share())

        top_pose_results_file = Path(self._config.top_pose_results_file)
        #top_pose_results_writer = PoseResultsWriterSink(top_pose_results_file)
        offset_pose_results_file = Path(self._config.offset_pose_results_file)
        #offset_pose_results_writer = PoseResultsWriterSink(offset_pose_results_file)

        top_pose_segment_writer = PoseSegmentWriter(segment_length_seconds=5.0)
        offset_pose_segment_writer = PoseSegmentWriter(segment_length_seconds=5.0)

        top_pose_results_writer_stream = Stream(
            rx.combine_latest(top_spool_stream.descriptor, top_pose_stream.descriptor),
            top_pose_stream.observable
        )
        offset_pose_results_writer_stream = Stream(
            rx.combine_latest(offset_spool_stream.descriptor, offset_pose_stream.descriptor),
            offset_pose_stream.observable
        )

        top_pose_segment_stream = top_pose_segment_writer.pipe(top_pose_results_writer_stream).pipe(ops.observe_on(_main_scheduler), ops.share())
        offset_pose_segment_stream = offset_pose_segment_writer.pipe(offset_pose_results_writer_stream).pipe(ops.observe_on(_main_scheduler), ops.share())

        top_pose_sink = DoNothingSink()
        offset_pose_sink = DoNothingSink()

        top_pose_results_sub = top_pose_sink.subscribe(top_pose_segment_stream)
        offset_pose_results_sub = offset_pose_sink.subscribe(offset_pose_segment_stream)

        data_descriptor = rx.combine_latest(
            top_video_segment_stream.descriptor,
            top_pose_segment_stream.descriptor
        ).pipe(
            ops.map(lambda vp: (HomecageDataSegmentFormat(vp[0], vp[1], 5.0)))
        )

        def _build_data_segment(segments):
            top_video_segment, offset_video_segment, top_pose_segment, offset_pose_segment = segments
            assert top_video_segment.segment_index == offset_video_segment.segment_index == top_pose_segment.segment_index == offset_pose_segment.segment_index
            return HomecageDataSegment(
                top_video_segment.segment_index,
                TopDataSegment(
                    TopCameraDataSegment(top_video_segment.file_path, None, top_pose_segment.file_path),
                    TopCameraDataSegment(offset_video_segment.file_path, None, offset_pose_segment.file_path),
                    None
                )
            )

        data_observable = rx.zip(
            top_video_segment_stream.observable,
            offset_video_segment_stream.observable,
            top_pose_segment_stream.observable,
            offset_pose_segment_stream.observable
        ).pipe(
            ops.map(_build_data_segment),
            ops.do_action(print)
        )
        data_segment_stream = Stream(data_descriptor, data_observable)

        recording_id = str(uuid.uuid4())
        def segment_folder_factory(segment_index: int) -> Path:
            folder = Path(f"recordings/homecage/segments/{recording_id}_segment_{segment_index}")
            return folder

        data_segment_sink = HomecageLiveResultsSink(segment_folder_factory)
        data_segment_sub = data_segment_sink.subscribe(data_segment_stream)

        disposable = CompositeDisposable(top_video_sub, offset_video_sub, top_pose_results_sub, offset_pose_results_sub)
        primary_done = rx.zip(top_video_sub.done, offset_video_sub.done)
        secondary_done = rx.zip(top_pose_results_sub.done, offset_pose_results_sub.done, data_segment_sub.done)

        return PipelineSubscription(disposable, primary_done, secondary_done)

    def dispose(self):
        if self._mouse_model_lease:
            self._mouse_model_lease.dispose()
            self._mouse_model_lease = None

        if self._env_model_lease:
            self._env_model_lease.dispose()
            self._env_model_lease = None
