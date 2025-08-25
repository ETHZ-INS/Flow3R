from dataclasses import dataclass
from typing import ClassVar


@dataclass
class SaveVideoConfig:
    CODECS: ClassVar[dict] = {
        'mp4v': 'mp4v',
        'fmp4': 'FMP4',
    }

    file_path_template: str = "{base_folder}/{recording_name}/{camera_name}.mp4"
    video_codec: str = "mp4v"

    def to_dict(self) -> dict:
        return {
            'file_path_template': self.file_path_template,
            'video_codec': self.video_codec
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SaveVideoConfig':
        return cls(
            file_path_template=data.get('file_path_template', cls.file_path_template),
            video_codec=data.get('video_codec', cls.video_codec)
        )
