from pathlib import Path

from py3r.media.streaming.observables.reader_observable import reader_observable
from py3r.media.types import VideoFrame
from py3r.media.video.pylon_camera_source import PylonCameraSource as BasePylonCameraSource
from reactivex import operators as ops

from flow3r.core.source.abc.source import ISource
from flow3r.core.streaming.stream import Stream
from flow3r.plugins.core.source.video.pylon.config import PylonCameraSourceConfig
from flow3r.plugins.core.typing.video import VideoFormat


class PylonCameraSource(ISource[VideoFormat, VideoFrame]):
    def __init__(self, config: PylonCameraSourceConfig):
        self._video_source = BasePylonCameraSource(config.device, Path(config.config_file) if config.config_file else None)
        fmt = VideoFormat(
            self._video_source.get_size(),
            self._video_source.get_fps(),
            "mono8" if self._video_source.get_num_channels() == 1 else "rgb24"
        )
        last_index = None
        def check_consecutive(frame: VideoFrame):
            nonlocal last_index
            frame_index = frame.frame_index
            if last_index is None:
                print(f"First frame index: {frame_index}")
            elif frame_index - last_index != 1:
                print(f"Frame index gap: {frame_index - last_index}")
            last_index = frame_index

        data = reader_observable(self._video_source, read_timeout_seconds=2.0, max_consecutive_errors=30).pipe(ops.do_action(check_consecutive)).pipe(ops.share())
        self._stream = Stream(fmt, data)

    @property
    def stream(self) -> Stream[VideoFormat, VideoFrame]:
        return self._stream

    def open(self):
        pass

    def close(self):
        pass
