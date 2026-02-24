from typing import Protocol, Callable, TypeVar, Tuple

from PySide6.QtWidgets import QWidget

from flow3r.core.api.app.app_context import IAppContext
from flow3r.core.pipeline.abc.pipeline import IPipeline

TConfig = TypeVar("TConfig")  # TODO: bound to config type interface
TPipeline = TypeVar("TPipeline", bound=IPipeline)


class IPipelineType(Protocol[TConfig, TPipeline]):
    @property
    def name(self) -> str: ...
    @property
    def category(self) -> Tuple[str, ...]: ...
    def get_config_factory(self) -> Callable[[], TConfig]: ...
    def get_config_widget_factory(self) -> Callable[[IAppContext, TConfig, QWidget], QWidget]: ...
    def get_pipeline_factory(self) -> Callable[[], IPipeline]: ...
