from typing import Dict

from aaaflow3r.core.api.plugins.pipeline_type_registry import IPipelineTypeRegistry
from aaaflow3r.core.pipeline.abc.pipeline_type import IPipelineType


class PipelineTypeRegistry(IPipelineTypeRegistry):
    def __init__(self):
        self._pipeline_types = {}

    def register(self, pipeline_type: IPipelineType):
        self._pipeline_types[pipeline_type.name] = pipeline_type

    def get_pipeline_types(self) -> Dict[str, IPipelineType]:
        return self._pipeline_types
