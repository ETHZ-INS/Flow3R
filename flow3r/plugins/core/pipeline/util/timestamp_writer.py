from pathlib import Path
from typing import TextIO, Optional


class TimestampWriter:
    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._file_handle: Optional[TextIO] = None
        self._frame_index = 0

    def open(self):
        if self._file_handle is not None:
            return

        self._frame_index = 0
        self._file_handle = self._file_path.open("w")

    def write(self, timestamp: float):
        if self._file_handle is None:
            raise RuntimeError("TimestampWriter is not open")

        self._file_handle.write(f"{self._frame_index},{timestamp}\n")
        self._frame_index += 1

    def close(self):
        if self._file_handle is None:
            return

        self._file_handle.close()
        self._file_handle = None