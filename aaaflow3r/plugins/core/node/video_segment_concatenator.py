import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from aaaflow3r.core.streaming.abc.sink import Sink
from aaaflow3r.plugins.core.node.video_segment_writer import VideoSegment
from aaaflow3r.plugins.core.typing.video_segment import VideoSegmentFormat


def concat_segments(segments: list[Path], output_file: Path) -> None:
    if len(segments) == 0:
        return

    if len(segments) == 1:
        shutil.copy(segments[0], output_file)
        return

    list_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt', prefix='ffmpeg_concat_')
    for chunk_file in segments:
        list_file.write(f"file '{chunk_file}'\n")
    list_file.close()

    try:
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file.name),
            '-c', 'copy',
            '-y',  # Overwrite output file if it exists
            '-hide_banner',
            '-loglevel', 'error',
            str(output_file.absolute())
        ]
        subprocess.run(cmd, check=True)
    finally:
        os.remove(str(list_file.name))


class VideoSegmentConcatenator(Sink[VideoSegmentFormat, VideoSegment]):
    def __init__(self, output_file: Path, *, delete_segments: bool = False):
        self._output_file = output_file
        self._delete_segments = delete_segments
        self._segments: list[Path] = []
        self._closed = False

    def setup(self, desc: VideoSegmentFormat) -> None:
        self._segments = []
        self._closed = False

    def on_next(self, seg: VideoSegment) -> None:
        self._segments.append(seg.file_path)

    def cleanup(self) -> None:
        # base class guarantees this runs exactly once on completed/error/dispose
        self._finalize_once()

    def _finalize_once(self) -> None:
        if self._closed:
            return
        self._closed = True

        # If no segments, do nothing or create empty file
        if not self._segments:
            return

        # Concat (best to use ffmpeg concat demuxer for lossless concat)
        concat_segments(self._segments, self._output_file)

        if self._delete_segments:
            for p in self._segments:
                try: p.unlink()
                except OSError: pass
