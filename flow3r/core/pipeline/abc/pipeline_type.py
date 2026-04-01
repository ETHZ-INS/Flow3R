from dataclasses import dataclass
from typing import Protocol, Callable, TypeVar, Tuple, Generic

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
    @property
    def config_factory(self) -> Callable[[], TConfig]: ...
    @property
    def config_widget_factory(self) -> Callable[[IAppContext, TConfig, QWidget], QWidget]: ...
    @property
    def pipeline_factory(self) -> Callable[[], IPipeline]: ...


@dataclass
class PipelineType(Generic[TConfig, TPipeline]):
    name: str
    category: Tuple[str, ...]
    config_factory: Callable[[], TConfig]
    config_widget_factory: Callable[[IAppContext, TConfig, QWidget], QWidget]
    pipeline_factory: Callable[[], IPipeline]
