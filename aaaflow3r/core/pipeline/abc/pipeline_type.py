from typing import Protocol, Callable, TypeVar

from PySide6.QtWidgets import QWidget

from aaaflow3r.core.pipeline.abc.pipeline import IPipeline

TConfig = TypeVar("TConfig")  # TODO: bound to config type interface
TPipeline = TypeVar("TPipeline", bound=IPipeline)


class IPipelineType(Protocol[TConfig, TPipeline]):
    @property
    def name(self) -> str: ...
    @property
    def category(self) -> str: ...
    def get_config_factory(self) -> Callable[[], TConfig]: ...
    def get_config_widget_factory(self) -> Callable[[TConfig, QWidget], QWidget]: ...
    def get_pipeline_factory(self) -> Callable[[], IPipeline]: ...
