from typing import List

from aaaflow3r.core.pipeline.pipeline_config import PipelineConfig


class PipelineConfigView:
    def __init__(self, app: "AppConfigView", pipeline_config: PipelineConfig):
        self._app = app
        self._pipeline_config = pipeline_config

    @property
    def app(self) -> "AppConfigView":
        return self._app

    @property
    def config(self) -> PipelineConfig:
        return self._pipeline_config

    @property
    def pipeline_id(self) -> str:
        return self._pipeline_config.id

    @property
    def active_groups(self) -> List["CameraConfigView"]:
        return [group for group in self.app.groups.values() if group.active and group.pipeline_id == self.pipeline_id]

    @property
    def active(self):
        return bool(self.active_groups)
