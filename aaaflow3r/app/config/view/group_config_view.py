from typing import List

from aaaflow3r.app.config.recording_config import RecordingConfig


class GroupConfigView:
    def __init__(self, app: "AppConfigView", group_id: str, recording_config: RecordingConfig):
        self._app = app
        self._group_id = group_id
        self._recording_config = recording_config

    @property
    def app(self) -> "AppConfigView":
        return self._app

    @property
    def group_id(self) -> str:
        return self._group_id

    @property
    def cameras(self) -> List["CameraConfigView"]:
        return [camera for camera in self.app.cameras.values() if camera.active and camera.group_id == self._group_id]

    @property
    def active(self):
        return bool(self.cameras)

    @property
    def recording_config(self) -> RecordingConfig:
        return self._recording_config
