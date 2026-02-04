from typing import List, Optional

from aaaflow3r.app.config.group_config import GroupConfig
from aaaflow3r.app.config.recording_config import RecordingConfig
from aaaflow3r.app.config.view.pipeline_config_view import PipelineConfigView


class GroupConfigView:
    def __init__(self, app: "AppConfigView", group_config: GroupConfig, implicit: bool = False):
        self._app = app
        self._group_config = group_config
        self._implicit = implicit

    @property
    def app(self) -> "AppConfigView":
        return self._app

    @property
    def group_id(self) -> str:
        return self._group_config.id

    @property
    def cameras(self) -> List["CameraConfigView"]:
        return [
            camera for camera in self.app.cameras.values()
            if camera.active and camera.group_id == self.group_id
        ]

    @property
    def pipeline(self) -> Optional[PipelineConfigView]:
        if self._group_config.pipeline_id is None:
            return None
        return self.app.pipelines[self._group_config.pipeline_id]

    @property
    def active(self):
        return bool(self.cameras)

    @property
    def recording_config(self) -> RecordingConfig:
        return self._group_config.recording_config
