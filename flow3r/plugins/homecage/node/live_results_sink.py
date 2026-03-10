import json
from pathlib import Path
from typing import Callable

from flow3r.core.streaming.abc.sink import Sink
from flow3r.plugins.homecage.typing.data_segment import HomecageDataSegmentFormat, HomecageDataSegment


SegmentFolderFactory = Callable[[int], Path]


class HomecageLiveResultsSink(Sink[HomecageDataSegmentFormat, HomecageDataSegment]):
    def __init__(self, segment_folder_factory: SegmentFolderFactory):
        super().__init__()
        self._segment_folder_factory = segment_folder_factory

    def on_completed(self) -> None:
        print(f"HomecageLiveResultsSink completed")

    def setup(self, desc: HomecageDataSegmentFormat) -> None:
        pass

    def on_next(self, item: HomecageDataSegment) -> None:
        segment_folder = self._segment_folder_factory(item.segment_index)
        segment_folder.mkdir(parents=True, exist_ok=True)

        data_file = segment_folder / "data.json"
        temp_file = segment_folder / "data.tmp"

        with temp_file.open("w+") as f:
            data = {
                "top_video_file": str(item.top_data_segment.left.video_file.absolute()),
                "offset_video_file": str(item.top_data_segment.right.video_file.absolute()),
                "top_pose_file": str(item.top_data_segment.left.pose_file.absolute()),
                "offset_pose_file": str(item.top_data_segment.right.pose_file.absolute()),
                "calibration_file": str(item.top_data_segment.calibration_file.absolute())
            }
            json.dump(data, f, indent=4)

        temp_file.rename(data_file)

    def cleanup(self) -> None:
        pass
