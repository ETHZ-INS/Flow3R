import subprocess
from pathlib import Path
from typing import Tuple, Any

from flow3r.core.streaming.abc.sink import Sink


class VideoAudioMuxerSink(Sink[Any, Tuple[Path, Path]]):
    def __init__(self, target_video_file: Path, remove_input_files: bool = False):
        super().__init__()
        self._video_file = target_video_file
        self._remove_input_files = remove_input_files

    def setup(self, desc: Any) -> None:
        pass

    def on_next(self, item: Tuple[Path, Path]) -> None:
        video_file, audio_file = item
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", str(video_file),
            "-i", str(audio_file),
            "-c:v", "copy",
            "-c:a", "copy",
            str(self._video_file)
        ]
        subprocess.run(cmd, check=True)

        if self._remove_input_files:
            video_file.unlink()
            audio_file.unlink()

    def cleanup(self) -> None:
        pass