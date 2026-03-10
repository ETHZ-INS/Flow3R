from flow3r.app.config.source_config import SourceConfig


class SourceConfigView:
    def __init__(self, app: "AppConfigView", source: SourceConfig):
        self._app = app
        self._source = source

    @property
    def app(self) -> "AppConfigView":
        return self._app

    @property
    def source_id(self) -> str:
        return self._source.id

    @property
    def active(self) -> bool:
        return self._source.active

    @property
    def group_id(self) -> str:
        # If a camera does not have a group assigned, it forms its own group
        return self._source.group_id if self._source.group_id is not None else self.source_id

    @property
    def group(self) -> "GroupConfigView":
        return self.app.groups[self.group_id]
