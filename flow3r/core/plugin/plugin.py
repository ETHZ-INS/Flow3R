from typing import Protocol

from flow3r.core.api.plugins.plugins import IPluginAPI


class IPlugin(Protocol):
    @property
    def name(self) -> str: ...
    def initialize(self, api: IPluginAPI): ...
