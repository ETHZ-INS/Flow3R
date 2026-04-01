from typing import Callable

from PySide6.QtWidgets import QWidget

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.pipeline.abc.pipeline_type import IPipelineType
from flow3r.plugins.homecage.pipeline.homecage_analysis.config import HomecageAnalysisConfig
from flow3r.plugins.homecage.pipeline.homecage_analysis.config_widget import HomecageAnalysisConfigWidget
from flow3r.plugins.homecage.pipeline.homecage_analysis.pipeline import HomecageAnalysisPipeline


class HomecageAnalysisPipelineType(IPipelineType[HomecageAnalysisConfig, HomecageAnalysisPipeline]):
    @property
    def name(self) -> str:
        return "Homecage Analysis"

    @property
    def config_factory(self) -> Callable[[], HomecageAnalysisConfig]:
        return HomecageAnalysisConfig

    @property
    def config_widget_factory(self) -> Callable[[IAppContext, HomecageAnalysisConfig, QWidget], QWidget]:
        return HomecageAnalysisConfigWidget

    @property
    def pipeline_factory(self) -> Callable[[], HomecageAnalysisPipeline]:
        return HomecageAnalysisPipeline
