from typing import Protocol

from flow3r.core.pipeline.abc.pipeline_type import IPipelineType


class IPipelineTypeRegistry(Protocol):
    def register(self, pipeline_type: IPipelineType): ...
