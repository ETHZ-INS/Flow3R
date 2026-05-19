from flow3r.core.api.plugins.plugins import IPluginAPI
from flow3r.core.plugin.plugin import IPlugin
from flow3r.core.source.abc.source_type import SourceType
from flow3r.plugins.homecage.pipeline.homecage_analysis.config import HomecageAnalysisConfig
from flow3r.plugins.homecage.pipeline.homecage_analysis.pipeline_type import HomecageAnalysisPipelineType
from flow3r.plugins.homecage.pipeline.straight_to_disk_homecage_analysis.config import SHomecageAnalysisConfig
from flow3r.plugins.homecage.pipeline.straight_to_disk_homecage_analysis.pipeline_type import \
    SHomecageAnalysisPipelineType
from flow3r.plugins.homecage.source.dummy.config import DummySourceConfig
from flow3r.plugins.homecage.source.dummy.config_widget import DummySourceConfigWidget
from flow3r.plugins.homecage.source.dummy.source import DummySource

DUMMY_SOURCE_TYPE = SourceType(
    name="Dummy Source",
    category=("Dummy",),
    config_factory=DummySourceConfig,
    config_widget_factory=DummySourceConfigWidget,
    source_factory=DummySource
)


class HomecagePlugin(IPlugin):
    @property
    def name(self) -> str:
        return "ETH3RHub Homecage"

    def initialize(self, api: IPluginAPI):
        api.config_types.register(DummySourceConfig.TYPE_ID, DummySourceConfig)
        api.config_types.register(HomecageAnalysisConfig.TYPE_ID, HomecageAnalysisConfig)
        api.config_types.register(SHomecageAnalysisConfig.TYPE_ID, SHomecageAnalysisConfig)

        api.source_types.register(DUMMY_SOURCE_TYPE)

        api.pipeline_types.register(HomecageAnalysisPipelineType())
        api.pipeline_types.register(SHomecageAnalysisPipelineType())
