from flow3r.core.api.plugins.plugins import IPluginAPI


class IPlugin:
    def initialize(self, api: IPluginAPI): ...
