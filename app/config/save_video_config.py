from dataclasses import dataclass
from typing import ClassVar

from app.placeholder_formatter import PlaceholderFormatter


@dataclass
class SaveVideoConfig:
    CODECS: ClassVar[dict] = {
        'mp4v': 'mp4v',
        'fmp4': 'FMP4',
    }

    file_path: str = "{base_folder}/{recording_name}/{camera_name}.mp4"
    video_codec: str = "mp4v"

    def to_dict(self) -> dict:
        return {
            'file_path': self.file_path,
            'video_codec': self.video_codec
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SaveVideoConfig':
        return cls(
            file_path=data.get('file_path', cls.file_path),
            video_codec=data.get('video_codec', cls.video_codec)
        )

    def get_required_variables(self) -> set:
        return PlaceholderFormatter(self.file_path).get_placeholders()
