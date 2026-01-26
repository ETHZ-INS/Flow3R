from pathlib import Path
from typing import List, Any, Optional

from py3r.media.streaming.operators import adaptive_pace
from py3r.pose.core.model.mock_pose_model import MockPoseModel
from py3r.pose.core.streaming.pose_estimation_transform import PoseEstimationTransform
from py3r.pose.core.streaming.pose_render_transform import PoseRenderTransform
from py3r.pose.core.types import PoseInstance, PoseInstanceType, PosePoint
from py3r.pose.core.visualization.pose_renderer import PoseRenderer
from py3r.pose.yolo.model.staged_yolo_pose_model import StagedYoloPoseModel
from py3r.pose.yolo.model.yolo_pose_model import YoloPoseModel
from reactivex import operators as ops

from py3r.media.streaming.video.video_writer_observer import VideoWriterObserver
from py3r.media.video.ffmpeg_video_file_writer import FFmpegVideoFileWriter

from aaaflow3r.core.api.app.app_context import IAppContext
from aaaflow3r.core.pipeline.abc.pipeline import IPipeline
from aaaflow3r.core.streaming.abc.stream import IStream
from aaaflow3r.core.streaming.stream import Stream
from aaaflow3r.core.visualization.abc.visualizer_handle import IVisualizerHandle
from aaaflow3r.plugins.core.typing.video import VideoFormat
from aaaflow3r.plugins.pose_estimation.pipeline.pose_estimation.config import PoseEstimationConfig


class PoseEstimationPipeline(IPipeline[PoseEstimationConfig]):
    def __init__(self):
        self._widget_handle: Optional[IVisualizerHandle] = None
        self._config: Optional[PoseEstimationConfig] = None

    def configure(self, app_context: IAppContext, config: PoseEstimationConfig):
        self._config = config
        if not self._widget_handle:
            self._widget_handle = app_context.widget_service.get_visualizer_handle("Video", "my_video", "my_session")

    def build(self, app_context: IAppContext, sources: List[IStream]) -> Any:
        assert len(sources) == 1
        source = sources[0]

        def setup(desc: VideoFormat):
            print("PoseEstimationPipeline setup")
            shared_source = Stream(source.descriptor, source.observable.pipe(ops.share()))

            model = YoloPoseModel.from_folder(Path("C:/Users/Me/AppData/Local/ETH3RHub/models/bohaceklab/pose_estimation/mouse/mouse_top_main"))
            staged_model = StagedYoloPoseModel(model, max_batch=4, input_channels=1)

            #triangle_type = PoseInstanceType("triangle", ["p1", "p2", "p3"], skeleton=[(0, 1), (1, 2), (2, 0)])

            #pose_renderer = PoseRenderer([triangle_type])
            pose_renderer = PoseRenderer(model.get_instance_types())

            #box = (0.25 * desc.size[0], 0.25 * desc.size[1], 0.75 * desc.size[0], 0.75 * desc.size[1])
            #points = [
            #    PosePoint(0.5 * desc.size[0], 0.35 * desc.size[1], 0.9),
            #    PosePoint(0.3 * desc.size[0], 0.65 * desc.size[1], 0.9),
            #    PosePoint(0.7 * desc.size[0], 0.65 * desc.size[1], 0.9)
            #]

            #model = MockPoseModel([
            #    PoseInstance("triangle_1", triangle_type, box, points, 0.95)
            #])

            pose_estimation_transform = PoseEstimationTransform(staged_model, batch_size=4)
            pose_render_transform = PoseRenderTransform(pose_renderer)

            poses = shared_source.observable.pipe(pose_estimation_transform)
            pose_visualizations = poses.pipe(adaptive_pace(1/desc.fps), pose_render_transform(shared_source.observable))
            pose_stream = Stream(source.descriptor, pose_visualizations)

            self._widget_handle.subscribe(pose_stream)

            writer = FFmpegVideoFileWriter(Path(self._config.video_file), desc.size, desc.fps, grayscale=desc.fmt=="mono8", quality="high")
            observer = VideoWriterObserver(writer)
            shared_source.observable.pipe(observer.using).subscribe(observer)

        source.descriptor.subscribe(setup)

    def dispose(self):
        if self._widget_handle:
            self._widget_handle.dispose()
