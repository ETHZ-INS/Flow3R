from functools import cached_property
from typing import Dict

from aaaflow3r.app.config.app_config import AppConfig
from aaaflow3r.app.config.view.group_config_view import GroupConfigView
from aaaflow3r.app.config.view.pipeline_config_view import PipelineConfigView
from aaaflow3r.app.config.view.source_config_view import SourceConfigView


class AppConfigView:
    def __init__(self, app_config: AppConfig):
        self._app = app_config

    @cached_property
    def sources(self) -> Dict[str, SourceConfigView]:
        return {
            source_id: SourceConfigView(self, source_config)
            for source_id, source_config in self._app.sources.items()
        }

    @cached_property
    def groups(self) -> Dict[str, GroupConfigView]:
        return self.explicit_groups | self.implicit_groups

    @cached_property
    def pipelines(self) -> Dict[str, PipelineConfigView]:
        return {
            pipeline_id: PipelineConfigView(self, pipeline_config)
            for pipeline_id, pipeline_config in self._app.pipelines.items()
        }

    @cached_property
    def explicit_groups(self) -> Dict[str, GroupConfigView]:
        return {
            group_id: GroupConfigView(self, group_config, implicit=False)
            for group_id, group_config in self._app.groups.items()
        }


    @cached_property
    def implicit_groups(self) -> Dict[str, GroupConfigView]:
        return {
            source_id: GroupConfigView(self, group_config, implicit=True)
            for source_id, group_config in self._app.implicit_groups.items()
        }
