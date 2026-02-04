from pathlib import Path
from typing import Optional

from py3r.pose.core.serialization.dynamic_csv_writer import DynamicPoseCSVWriter
from py3r.pose.core.types import VideoFramePoses

from aaaflow3r.core.streaming.abc.sink import Sink
from aaaflow3r.plugins.core.typing.video import VideoFormat


class PoseResultsWriterSink(Sink[VideoFormat, VideoFramePoses]):
    def __init__(self, results_file: Path):
        super().__init__()
        self._results_file = results_file
        self._writer: Optional[DynamicPoseCSVWriter] = None

    def setup(self, desc: VideoFormat) -> None:
        self._writer = DynamicPoseCSVWriter(self._results_file)

    def on_next(self, item: VideoFramePoses) -> None:
        assert self._writer is not None
        try:
            self._writer.write(item)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def cleanup(self) -> None:
        if self._writer is not None:
            self._writer.close()
            self._writer = None
