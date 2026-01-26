from functools import cached_property
from typing import Dict

from aaaflow3r.app.config.app_config import AppConfig
from aaaflow3r.app.config.view.group_config_view import GroupConfigView
from aaaflow3r.app.config.view.source_config_view import SourceConfigView


class AppConfigView:
    def __init__(self, app_config: AppConfig):
        self._app = app_config

    @cached_property
    def sources(self) -> Dict[str, SourceConfigView]:
        return {source_id: SourceConfigView(self, source) for source_id, source in self._app.sources.items()}

    @cached_property
    def groups(self) -> Dict[str, GroupConfigView]:
        return {
            group_id: GroupConfigView(self, group_id, group.recording_config)
            for group_id, group in self._app.groups.items()
        } | self._implicit_groups

    @cached_property
    def _implicit_groups(self) -> Dict[str, GroupConfigView]:
        return {
            source_id: GroupConfigView(self, source_id, self._app.default_recording_config)
            for source_id, source in self._app.sources.items()
            if source.group_id is None
        }
