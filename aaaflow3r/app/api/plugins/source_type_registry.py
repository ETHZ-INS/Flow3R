from typing import Dict

from aaaflow3r.core.api.plugins.source_type_registry import ISourceTypeRegistry
from aaaflow3r.core.source.abc.source_type import ISourceType


class SourceTypeRegistry(ISourceTypeRegistry):
    def __init__(self):
        self._source_types = {}

    def register(self, source_type: ISourceType):
        self._source_types[source_type.name] = source_type

    def get_source_types(self) -> Dict[str, ISourceType]:
        return self._source_types
