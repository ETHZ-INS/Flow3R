from dataclasses import dataclass

from app.config.config_base import ConfigBase
from app.placeholder_formatter import PlaceholderFormatter


@dataclass
class PoseEstimationConfig(ConfigBase):
    preset_id: str = None
    save_to_file: bool = True
    save_file: str = "pose_results.csv"

    @property
    def error(self) -> str | None:
        if self.preset_id is None:
            return "Pose estimation preset is not selected."
        if self.save_to_file and not self.save_file:
            return "Save file is not selected."
        return None

    def _extra_to_dict(self) -> dict:
        return {
            "preset_id": self.preset_id,
            "save_to_file": self.save_to_file,
            "save_file": self.save_file
        }

    @classmethod
    def _extra_from_dict(cls, data: dict) -> dict:
        return {
            "preset_id": data.get("preset_id", cls.preset_id),
            "save_to_file": data.get("save_to_file", cls.save_to_file),
            "save_file": data.get("save_file", cls.save_file)
        }

    def get_required_variables(self) -> set:
        return PlaceholderFormatter(self.save_file).get_placeholders()
